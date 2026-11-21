"""Everything the LLM is allowed to spawn. The LLM only ever sees ids + blurbs from here.

To add content: add a Spawnable to one of the lists. The LLM schema, the prompt and the
validation all read from these dicts, so nothing else needs to change.
"""

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, replace

from engine.data import sprites as sp
from engine.combat.attacks import Attack, attack
from engine.models import Character, Entity, Item, Potion, Stats, Weapon


@dataclass(frozen=True)
class Spawnable:
    id: str
    blurb: str  # one line the LLM reads when choosing
    make: Callable[[], Entity]


def _enemy(
    name: str, desc: str, art: dict, stats: Stats, line: str, attacks: list[Attack], resist: dict[str, float] | None = None
) -> Callable[[], Character]:
    return lambda: Character(
        name=name,
        description=desc,
        art=art,
        stats=replace(stats),
        hostile=True,
        dialogue=[line],
        attacks=deepcopy(attacks),
        resistances=dict(resist or {}),
    )


def _npc(name: str, desc: str, art: dict, stats: Stats, lines: list[str]) -> Callable[[], Character]:
    return lambda: Character(name=name, description=desc, art=art, stats=replace(stats), dialogue=list(lines))


def _item(name: str, desc: str, art: dict, buffs: Stats, value: int) -> Callable[[], Item]:
    return lambda: Item(name=name, description=desc, art=art, stats=replace(buffs), value=value)


def _weapon(name: str, desc: str, art: dict, buffs: Stats, value: int, hit: Attack) -> Callable[[], Weapon]:
    return lambda: Weapon(name=name, description=desc, art=art, stats=replace(buffs), value=value, attack=deepcopy(hit))


def _potion(name: str, desc: str, art: dict, value: int, heal: int) -> Callable[[], Potion]:
    return lambda: Potion(name=name, description=desc, art=art, value=value, heal=heal)


# Resistances: 0 immune, 0.5 resists, 2 weak. Keys are damage type ids or categories (engine/combat/damage.py).
ENEMIES = {
    s.id: s
    for s in [
        Spawnable("goblin", "weak, sneaky, steals", _enemy(
            "Goblin", "Small, green, very interested in your pockets.", sp.GOBLIN,
            Stats(strength=8, dexterity=14, max_hp=7), "Shiny! Give!",
            [attack("Rusty Dagger", "dexterity", ("1d4", "piercing"))],
        )),
        Spawnable("giant_rat", "weak, comes in packs", _enemy(
            "Giant Rat", "The size of a dog and twice as rude.", sp.GIANT_RAT,
            Stats(strength=6, dexterity=15, max_hp=4), "*squeak*",
            [attack("Bite", "dexterity", ("1d3", "sharp"))],
            {"fire": 1.5},
        )),
        Spawnable("skeleton", "medium, undead guard, weak to blunt weapons", _enemy(
            "Skeleton", "Rattles when it walks. Rattles when it doesn't.", sp.SKELETON,
            Stats(strength=12, dexterity=12, max_hp=13), "...",
            [attack("Bone Club", "strength", ("1d6", "dull"))],
            {"sharp": 0.5, "piercing": 0.5, "dull": 2.0, "water": 0.5},
        )),
        Spawnable("slime", "medium, slow, resists weapons, weak to fire", _enemy(
            "Slime", "Wobbles hungrily.", sp.SLIME,
            Stats(strength=12, dexterity=4, max_hp=18), "*blorp*",
            [attack("Engulf", "strength", ("1d4", "dull"), ("1d2", "water"))],
            {"physical": 0.5, "dull": 0.25, "fire": 2.0, "water": 0.0},
        )),
        Spawnable("cultist", "strong, casts fire magic, resists magic", _enemy(
            "Cultist", "Chants under their breath. It's not a nice chant.", sp.CULTIST,
            Stats(strength=10, dexterity=12, intelligence=14, max_hp=16), "The Deep One wakes!",
            [attack("Hellfire", "intelligence", ("1d8", "fire")), attack("Ritual Knife", "dexterity", ("1d4", "sharp"))],
            {"magic": 0.5, "water": 1.5},
        )),
    ]
}

NPCS = {
    s.id: s
    for s in [
        Spawnable("merchant", "friendly trader, sells junk", _npc("Old Merchant", "Sells things. Mostly junk.", sp.MERCHANT, Stats(charisma=14, max_hp=6), ["Wares! Fine wares!", "No refunds."])),
        Spawnable("hermit", "old sage, gives cryptic hints", _npc("Hermit", "Has lived down here too long.", sp.HERMIT, Stats(wisdom=16, max_hp=8), ["The deeper you go, the louder it dreams.", "Don't drink the green water."])),
    ]
}

ITEMS = {
    s.id: s
    for s in [
        Spawnable("rusty_sword", "weapon, sharp damage", _weapon(
            "Rusty Sword", "Seen better days, still pointy.", sp.SWORD, Stats(), 5,
            attack("Rusty Sword", "strength", ("1d6", "sharp")),
        )),
        Spawnable("war_hammer", "weapon, dull damage, good vs skeletons", _weapon(
            "War Hammer", "Every problem looks like a nail.", sp.HAMMER, Stats(), 15,
            attack("War Hammer", "strength", ("1d8", "dull")),
        )),
        Spawnable("spear", "weapon, piercing damage", _weapon(
            "Spear", "Keeps things at a polite distance.", sp.SPEAR, Stats(), 10,
            attack("Spear", "dexterity", ("1d6", "piercing")),
        )),
        Spawnable("flaming_sword", "rare weapon, sharp + fire damage", _weapon(
            "Flaming Sword", "Warm to the touch. Very warm.", sp.FLAMING_SWORD, Stats(), 60,
            attack("Flaming Sword", "strength", ("1d6", "sharp"), ("1d4", "fire")),
        )),
        Spawnable("red_potion", "healing potion", _potion("Red Potion", "Smells like cherries and regret. Heals 8.", sp.POTION, 10, heal=8)),
        Spawnable("owl_amulet", "trinket, +1 wisdom +1 charisma", _item("Owl Amulet", "The owl watches. The owl knows.", sp.AMULET, Stats(wisdom=1, charisma=1), 25)),
        Spawnable("brass_key", "opens something", _item("Brass Key", "Opens something, somewhere.", sp.KEY, Stats(), 1)),
        Spawnable("gold_coins", "treasure", _item("Gold Coins", "A small pile of gold.", sp.COINS, Stats(), 20)),
        Spawnable("torch", "light source, +1 wisdom", _item("Torch", "Keeps the dark honest.", sp.TORCH, Stats(wisdom=1), 2)),
    ]
}

# Look of the room. The UI maps these to colours (ui/src/view3d/themes.ts).
THEMES = {
    "cellar": "old stone cellar, barrels",
    "crypt": "cold tomb, bones",
    "cave": "rough natural cave",
    "sewer": "wet slimy tunnels",
}

# Shape of the room. engine/world/mapgen.py builds the tiles.
LAYOUTS = {
    "hall": "one big open room",
    "pillared": "big room with rows of pillars",
    "cross": "cross-shaped room",
    "cave": "twisty natural cavern",
    "chambers": "three rooms joined by doors",
}

FEATURES = {
    "water": "a pool of water",
    "rubble": "fallen rocks",
    "pillars": "a few stone pillars",
}


def make_party() -> list[Character]:
    """party[0] is the player."""
    player = Character(
        id="player",
        name="You",
        description="A hopeful adventurer.",
        art=sp.PLAYER,
        stats=Stats(strength=12, dexterity=14, constitution=12, intelligence=10, wisdom=11, charisma=13, max_hp=20),
        inventory=[ITEMS["rusty_sword"].make(), ITEMS["red_potion"].make()],
        # Spells the player knows (weapons in the inventory add more attacks).
        attacks=[
            attack("Fire Bolt", "intelligence", ("1d6", "fire")),
            attack("Water Jet", "intelligence", ("1d4", "water")),
        ],
    )
    brena = Character(
        id="brena",
        name="Brena",
        description="Dwarf cleric. Hums when nervous.",
        art=sp.BRENA,
        stats=Stats(strength=14, dexterity=8, constitution=15, intelligence=10, wisdom=15, charisma=9, max_hp=24),
        dialogue=["Stay behind me, lad."],
    )
    return [player, brena]
