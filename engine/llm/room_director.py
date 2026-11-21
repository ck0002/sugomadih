"""The LLM as dungeon master: it picks what the next room looks like and what's in it.

Flow: catalog ids -> JSON schema (enums) + short prompt -> LLM -> parse_room_plan() -> RoomPlan.
The schema, prompt and validation are all generated from engine/data/catalog.py.
"""

import logging
from dataclasses import dataclass, field

from engine.data.catalog import ENEMIES, FEATURES, ITEMS, LAYOUTS, NPCS, THEMES
from engine.llm.client import LLMClient, LLMError
from engine.models import Character

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


def room_schema() -> dict:
    """JSON schema for the LLM's reply. Choices come first so the narration can describe them."""

    def ids(options: dict, max_items: int) -> dict:
        return {"type": "array", "items": {"enum": list(options)}, "maxItems": max_items}

    return {
        "type": "object",
        "properties": {
            "theme": {"enum": list(THEMES)},
            "layout": {"enum": list(LAYOUTS)},
            "features": ids(FEATURES, MAX_FEATURES),
            "enemies": ids(ENEMIES, MAX_ENEMIES),
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


def parse_room_plan(raw: object, source: str = "llm") -> RoomPlan:
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
        """Like text(), but if the model got cut off mid-sentence, end at the last full sentence."""
        value = text(key, limit, default)
        if value[-1] not in ".!?\"'":
            end = max(value.rfind(p) for p in ".!?")
            value = value[: end + 1] if end > 0 else value + "..."
        return value

    return RoomPlan(
        name=text("name", MAX_NAME, FALLBACK_NAMES[0]),
        narration=story("narration", MAX_NARRATION, FALLBACK_NARRATIONS[0]),
        layout=pick("layout", LAYOUTS, "hall"),
        theme=pick("theme", THEMES, "cellar"),
        features=pick_many("features", FEATURES, MAX_FEATURES, unique=True),
        enemies=pick_many("enemies", ENEMIES, MAX_ENEMIES),
        npcs=pick_many("npcs", NPCS, MAX_NPCS, unique=True),
        items=pick_many("items", ITEMS, MAX_ITEMS),
        source=source,
    )


class RoomDirector:
    """Asks the LLM for a room; if it fails, asks the fallback (e.g. RandomLLM) instead."""

    def __init__(self, llm: LLMClient, fallback: LLMClient):
        self.llm = llm
        self.fallback = fallback

    def plan(self, ctx: RoomContext) -> RoomPlan:
        schema, prompt = room_schema(), room_prompt(ctx)
        try:
            return parse_room_plan(self.llm.complete_json(SYSTEM_PROMPT, prompt, schema), "llm")
        except LLMError as e:
            log.warning("LLM failed, using fallback room: %s", e)
            return parse_room_plan(self.fallback.complete_json(SYSTEM_PROMPT, prompt, schema), "fallback")
