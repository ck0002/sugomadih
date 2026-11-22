"""The LLM as dungeon master: it picks what the next room looks like and what's in it.

Flow: catalog ids -> JSON schema (enums) + short prompt -> LLM -> parse_room_plan() -> RoomPlan.
The schema, prompt and validation are all generated from engine/data/catalog.py.
"""

import logging
from dataclasses import dataclass, field

from engine.data.catalog import ENEMIES, FEATURES, ITEMS, LAYOUTS, NPCS, THEMES
from engine.llm.client import LLMClient, LLMError
from engine.llm.text import clean_story
from engine.models import Character
from engine.story.campaign import CAMPAIGN, Chapter

log = logging.getLogger(__name__)

MAX_ENEMIES = 4
MAX_NPCS = 1
MAX_ITEMS = 3
MAX_FEATURES = 2
MAX_NAME = 40
MAX_NARRATION = 300

SYSTEM_PROMPT = (
    "You are the dungeon master of a fantasy dungeon crawler. "
    "Design the next room the party walks into. Only use the ids you are given. "
    "Pick choices that fit together (a theme, a layout, a few things in the room), "
    "then give the room a short evocative name and narrate the party entering it "
    "in at most 2 short sentences (under 40 words), mentioning what is in the room. Answer only with JSON."
)

FALLBACK_NAMES = ["A Quiet Chamber", "The Damp Hall", "Forgotten Passage", "The Echoing Room", "Dust and Bones"]
FALLBACK_NARRATIONS = [
    "You step into the next room. Something moves in the dark.",
    "The air changes as you enter. You are not alone here.",
    "Your torchlight finds the edges of a new room.",
]


@dataclass
class RoomContext:
    room_number: int
    party: list[Character]
    previous_room: str | None = None
    chapter: Chapter | None = None  # the story chapter this room belongs to (engine/story/campaign.py)
    chapter_number: int = 0  # 1-based
    chapter_count: int = 0
    story_so_far: list[str] = field(default_factory=list)  # titles of finished chapters


@dataclass
class RoomPlan:
    name: str
    narration: str
    layout: str
    theme: str
    features: list[str] = field(default_factory=list)
    enemies: list[str] = field(default_factory=list)
    npcs: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)
    source: str = "llm"  # "llm" or "fallback"


def room_schema(chapter: Chapter | None = None) -> dict:
    """JSON schema for the LLM's reply. Choices come first so the narration can describe them.
    A story chapter narrows the themes and the number of enemies."""
    themes = list(chapter.themes) if chapter else list(THEMES)
    max_enemies = chapter.max_enemies if chapter else MAX_ENEMIES

    def ids(options: dict, max_items: int) -> dict:
        return {"type": "array", "items": {"enum": list(options)}, "maxItems": max_items}

    return {
        "type": "object",
        "properties": {
            "theme": {"enum": themes},
            "layout": {"enum": list(LAYOUTS)},
            "features": ids(FEATURES, MAX_FEATURES),
            "enemies": ids(ENEMIES, max_enemies),
            "npcs": ids(NPCS, MAX_NPCS),
            "items": ids(ITEMS, MAX_ITEMS),
            "name": {"type": "string", "maxLength": MAX_NAME, "examples": FALLBACK_NAMES},
            "narration": {"type": "string", "maxLength": MAX_NARRATION, "examples": FALLBACK_NARRATIONS},
        },
        "required": ["theme", "layout", "features", "enemies", "npcs", "items", "name", "narration"],
    }


def room_prompt(ctx: RoomContext) -> str:
    def options(title: str, d: dict) -> str:
        return f"{title}: " + "; ".join(f"{k} ({v.blurb if hasattr(v, 'blurb') else v})" for k, v in d.items())

    party = ", ".join(f"{c.name} (hp {c.hp}/{c.total_stats().max_hp})" for c in ctx.party)
    if ctx.chapter:
        return story_room_prompt(ctx, party, options)
    if ctx.room_number <= 1:
        difficulty = "This is the first room: keep it gentle (0-1 weak enemies)."
    elif ctx.room_number <= 3:
        difficulty = "Early rooms: 1-2 weak or medium enemies."
    else:
        difficulty = "Deep in the dungeon: up to 4 enemies, stronger ones allowed."
    lines = [
        f"Room {ctx.room_number}. Party: {party}.",
        f"Previous room: {ctx.previous_room}." if ctx.previous_room else "The party has just entered the dungeon.",
        difficulty,
        options("Themes", THEMES),
        options("Layouts", LAYOUTS),
        options("Features (0-2)", FEATURES),
        options("Enemies", ENEMIES),
        options("NPCs (rare, 0-1)", NPCS),
        options("Items (0-3)", ITEMS),
    ]
    return "\n".join(lines)


def story_room_prompt(ctx: RoomContext, party: str, options) -> str:
    ch = ctx.chapter
    assert ch is not None
    guaranteed = [*ch.enemies, *ch.npcs, *ch.items]
    return "\n".join(
        [
            f"Story: {CAMPAIGN.premise}",
            f"So far: {', '.join(ctx.story_so_far)}." if ctx.story_so_far else "This is the start of the adventure.",
            f"Chapter {ctx.chapter_number} of {ctx.chapter_count}: {ch.title}. {ch.guidance}",
            f"The party's goal in this room: {ch.objective.text}.",
            f"Already in the room (mention them, don't pick them again): {', '.join(guaranteed)}." if guaranteed else "",
            f"Party: {party}. At most {ch.max_enemies} extra enemies.",
            options("Themes", {t: THEMES[t] for t in ch.themes}),
            options("Layouts", LAYOUTS),
            options("Features (0-2)", FEATURES),
            options("Enemies", ENEMIES),
            options("NPCs (rare, 0-1)", NPCS),
            options("Items (0-3)", ITEMS),
        ]
    ).replace("\n\n", "\n")


def parse_room_plan(raw: object, source: str = "llm", chapter: Chapter | None = None) -> RoomPlan:
    """Validate an LLM reply. Never raises: unknown ids are dropped, missing fields get defaults."""
    data = raw if isinstance(raw, dict) else {}

    def pick(key: str, options: dict, default: str) -> str:
        value = data.get(key)
        return value if isinstance(value, str) and value in options else default

    def pick_many(key: str, options: dict, limit: int, unique: bool = False) -> list[str]:
        values = data.get(key)
        if not isinstance(values, list):
            return []
        valid = [v for v in values if isinstance(v, str) and v in options]
        if unique:
            valid = list(dict.fromkeys(valid))
        return valid[:limit]

    def text(key: str, limit: int, default: str) -> str:
        value = data.get(key)
        value = " ".join(value.split()) if isinstance(value, str) else ""
        return value[:limit] if value else default

    def story(key: str, limit: int, default: str) -> str:
        return clean_story(data.get(key), limit) or default

    return RoomPlan(
        name=text("name", MAX_NAME, FALLBACK_NAMES[0]),
        narration=story("narration", MAX_NARRATION, FALLBACK_NARRATIONS[0]),
        layout=pick("layout", LAYOUTS, "hall"),
        theme=pick("theme", {t: 1 for t in chapter.themes} if chapter else THEMES, chapter.themes[0] if chapter else "cellar"),
        features=pick_many("features", FEATURES, MAX_FEATURES, unique=True),
        enemies=pick_many("enemies", ENEMIES, chapter.max_enemies if chapter else MAX_ENEMIES),
        npcs=pick_many("npcs", NPCS, MAX_NPCS, unique=True),
        items=pick_many("items", ITEMS, MAX_ITEMS),
        source=source,
    )


class RoomDirector:
    """Asks the LLM for a room; if it fails, asks the fallback (e.g. RandomLLM) instead."""

    def __init__(self, llm: LLMClient, fallback: LLMClient):
        self.llm = llm
        self.fallback = fallback
        self.use_llm = True  # debug: turn off to get instant random rooms

    def plan(self, ctx: RoomContext) -> RoomPlan:
        schema, prompt = room_schema(ctx.chapter), room_prompt(ctx)
        if self.use_llm:
            try:
                return parse_room_plan(self.llm.complete_json(SYSTEM_PROMPT, prompt, schema), "llm", ctx.chapter)
            except LLMError as e:
                log.warning("LLM failed, using fallback room: %s", e)
        return parse_room_plan(self.fallback.complete_json(SYSTEM_PROMPT, prompt, schema), "fallback", ctx.chapter)
