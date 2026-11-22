"""The campaign: a fixed story arc of chapters, one room each, ending in a boss fight.

The LLM still designs every room, but each chapter tells it what the room is about (guidance),
which themes fit, and Python guarantees the things the story needs are actually there (required spawns).
Exits stay sealed until the chapter's objective is done.

To change the story: edit CAMPAIGN below. Objective kinds:
    reach_exit                 walk out of the room
    collect     target=item    pick up an item with that catalog id
    talk        target=npc     bump into that NPC
    defeat_all                 no hostiles left in the room
    defeat_boss target=enemy   kill that enemy (on the last chapter this wins the game)
"""

from dataclasses import dataclass, field
from typing import Literal

ObjectiveKind = Literal["reach_exit", "collect", "talk", "defeat_all", "defeat_boss"]


@dataclass(frozen=True)
class Objective:
    kind: ObjectiveKind
    text: str  # shown to the player
    target: str | None = None  # catalog id for collect / talk / defeat_boss


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    objective: Objective
    guidance: str  # what the LLM should make of this room
    themes: tuple[str, ...]  # allowed room themes (catalog THEMES)
    max_enemies: int = 3
    enemies: tuple[str, ...] = ()  # always spawned (catalog ids, bosses allowed)
    npcs: tuple[str, ...] = ()
    items: tuple[str, ...] = ()
    dialogue: dict[str, tuple[str, ...]] = field(default_factory=dict)  # npc id -> story lines for this chapter


@dataclass(frozen=True)
class Campaign:
    title: str
    premise: str  # told to the LLM every room
    chapters: tuple[Chapter, ...]
    victory_text: str  # fallback epilogues when the LLM is offline
    defeat_text: str


CAMPAIGN = Campaign(
    title="The Dreaming Deep",
    premise=(
        "Beneath the Leaky Tankard tavern, a drowned cult is trying to wake the Deep One, a god that sleeps "
        "under the sea-caves. Travellers have gone missing. The party goes down to stop the High Priest "
        "before the god wakes."
    ),
    chapters=(
        Chapter(
            id="cellar",
            title="Beneath the Tankard",
            objective=Objective("reach_exit", "Find the way down"),
            guidance="The tavern cellar. Barrels, damp stone, whispers from below. A gentle start: a few rats at most.",
            themes=("cellar",),
            max_enemies=2,
        ),
        Chapter(
            id="crypt",
            title="The Sealed Crypt",
            objective=Objective("collect", "Find the Brass Key that unseals the stair", target="brass_key"),
            guidance="An old crypt under the cellar. The stair down is sealed; a brass key lies somewhere among the dead.",
            themes=("crypt",),
            items=("brass_key",),
        ),
        Chapter(
            id="hermit",
            title="The Hermit of the Caves",
            objective=Objective("talk", "Speak with the Hermit", target="hermit"),
            guidance="Natural caves. A half-mad hermit lives here and knows what the cult is doing.",
            themes=("cave",),
            npcs=("hermit",),
            dialogue={
                "hermit": (
                    "The cult drowns travellers to feed the Deep One's dreams. Their High Priest leads the rite below.",
                    "Fire won't burn him well, nor will spells. Crush him: blunt weapons break his ward.",
                    "Go down through the drowned tunnels. Hurry. The dreaming is getting louder.",
                )
            },
        ),
        Chapter(
            id="tunnels",
            title="The Drowned Tunnels",
            objective=Objective("reach_exit", "Get through the flooded tunnels"),
            guidance="Flooded sewer tunnels full of slimes and rats. The water is rising. A potion was left by a lost traveller.",
            themes=("sewer",),
            items=("red_potion",),
        ),
        Chapter(
            id="vigil",
            title="The Cult's Vigil",
            objective=Objective("defeat_all", "Defeat the cultists guarding the stair"),
            guidance="The cult's antechamber, lit by green candles. Cultists keep vigil before the final stair.",
            themes=("crypt", "cellar"),
            max_enemies=4,
            enemies=("cultist", "cultist"),
            items=("war_hammer",),
        ),
        Chapter(
            id="deep",
            title="The Dreaming Deep",
            objective=Objective("defeat_boss", "Stop the High Priest before the Deep One wakes", target="deep_priest"),
            guidance="A vast sea-cave where the High Priest performs the waking rite. This is the final battle.",
            themes=("cave",),
            max_enemies=1,
            enemies=("deep_priest",),
            items=("red_potion",),
        ),
    ),
    victory_text=(
        "The High Priest falls, and the rite falls apart with him. Far below, something vast turns over in its "
        "sleep and is still. You climb back up to the Leaky Tankard, where the ale is terrible and the cellar is quiet."
    ),
    defeat_text=(
        "The dark closes over you. Somewhere below, the chanting grows louder, and the Deep One stirs in its dreams. "
        "Perhaps the next party will be luckier."
    ),
)


def chapter_index(spec: str | int) -> int:
    """"3" / 3 -> index 2 (1-based chapters); "end" / "last" / "boss" -> the final chapter. Clamped."""
    last = len(CAMPAIGN.chapters) - 1
    if isinstance(spec, str):
        if spec.strip().lower() in ("end", "last", "boss", "final"):
            return last
        spec = int(spec)
    return max(0, min(last, spec - 1))
