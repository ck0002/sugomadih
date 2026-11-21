import random

import pytest

from engine.combat import dice
from engine.combat.ai import enemy_turns
from engine.combat.attacks import attack
from engine.combat.damage import DAMAGE_TYPES, DamageType, MagicDamage, PhysicalDamage, get_damage_type
from engine.combat.resolve import resolve_attack, tick_statuses
from engine.data.catalog import ENEMIES, ITEMS
from engine.game import Game
from engine.llm.client import RandomLLM
from engine.llm.room_director import RoomDirector
from engine.models import DIR_VECTORS, Character, MapState, Placement, Stats


class AlwaysRoll(random.Random):
    """rng whose randint always returns `value` (clamped to the range) and random() returns `chance`."""

    def __init__(self, value: int, chance: float = 0.0):
        super().__init__(0)
        self.value, self.chance = value, chance

    def randint(self, a: int, b: int) -> int:
        return max(a, min(b, self.value))

    def random(self) -> float:
        return min(self.chance, 0.999)  # never 1.0: Random's fallback algorithms would loop forever

    def choice(self, seq):
        return seq[0]


def dummy(**kw) -> Character:
    return Character(name="Dummy", stats=Stats(dexterity=10, max_hp=50), hostile=True, **kw)


# ---- damage type tree --------------------------------------------------------


def test_damage_types_form_an_abstract_tree() -> None:
    for abstract in (DamageType, PhysicalDamage, MagicDamage):
        with pytest.raises(TypeError):
            abstract()
    assert {t.id for t in DAMAGE_TYPES.values() if isinstance(t, PhysicalDamage)} == {"sharp", "dull", "piercing"}
    assert {t.id for t in DAMAGE_TYPES.values() if isinstance(t, MagicDamage)} == {"fire", "water"}
    assert get_damage_type("dull").lineage() == ["dull", "physical", "damage"]


def test_resistances_resolve_most_specific_first() -> None:
    target = dummy(resistances={"physical": 0.5, "dull": 2.0, "magic": 0.0})
    assert get_damage_type("sharp").multiplier(target) == 0.5  # from category
    assert get_damage_type("dull").multiplier(target) == 2.0  # specific wins
    assert get_damage_type("fire").multiplier(target) == 0.0
    assert get_damage_type("piercing").multiplier(target) == 1.0  # piercing ignores resistances


# ---- attacks -----------------------------------------------------------------


def test_hit_applies_resistance_per_damage_part() -> None:
    target = dummy(resistances={"fire": 2.0, "sharp": 0.5})
    attacker = Character(name="A", stats=Stats(strength=10))
    hit = attack("Flaming Sword", "strength", ("1d6", "sharp"), ("1d4", "fire"))
    result = resolve_attack(attacker, hit, target, AlwaysRoll(15, chance=1.0))  # d20=15 hits, dice roll max
    assert result.hit
    assert result.parts == [("sharp", 3), ("fire", 8)]  # 6*0.5, 4*2
    assert target.hp == 50 - 11


def test_natural_one_always_misses_and_crit_doubles_dice() -> None:
    attacker = Character(name="A", stats=Stats(strength=30))
    sword = attack("Sword", "strength", ("1d6", "sharp"))
    assert not resolve_attack(attacker, sword, dummy(), AlwaysRoll(1)).hit
    crit = resolve_attack(Character(name="A", stats=Stats(strength=10)), sword, dummy(), AlwaysRoll(20, chance=1.0))
    assert crit.crit and crit.damage == 12  # 2d6 at max


def test_piercing_crits_on_19() -> None:
    spear = attack("Spear", "dexterity", ("1d6", "piercing"))
    assert resolve_attack(Character(name="A"), spear, dummy(), AlwaysRoll(19)).crit


def test_fire_burns_and_water_puts_it_out() -> None:
    target = dummy()
    attacker = Character(name="A", stats=Stats(intelligence=10))
    resolve_attack(attacker, attack("Fire Bolt", "intelligence", ("1d6", "fire")), target, AlwaysRoll(15))
    assert target.has_status("burning")
    resolve_attack(attacker, attack("Water Jet", "intelligence", ("1d4", "water")), target, AlwaysRoll(15))
    assert not target.has_status("burning") and target.has_status("soaked")
    assert target.armor_class() == 10 - 2
    resolve_attack(attacker, attack("Fire Bolt", "intelligence", ("1d6", "fire")), target, AlwaysRoll(15))
    assert not target.has_status("soaked") and not target.has_status("burning")  # fire dried them instead


def test_dull_can_stun_and_stun_skips_a_turn() -> None:
    target = dummy()
    resolve_attack(Character(name="A"), attack("Club", "strength", ("1d6", "dull")), target, AlwaysRoll(15, chance=0.0))
    assert target.has_status("stunned")
    _, skip = tick_statuses(target)
    assert skip and not target.has_status("stunned")


def test_burning_ticks_damage_and_wears_off() -> None:
    target = dummy()
    resolve_attack(Character(name="A"), attack("Fire Bolt", "intelligence", ("1d6", "fire")), target, AlwaysRoll(15))
    hp = target.hp
    tick_statuses(target)
    tick_statuses(target)
    assert target.hp == hp - 4 and not target.has_status("burning")


def test_dice_parsing() -> None:
    assert dice.parse("1d6") == (1, 6, 0)
    assert dice.parse("2d4+1") == (2, 4, 1)
    assert dice.parse("d8-1") == (1, 8, -1)
    assert dice.parse("3") == (0, 0, 3)
    with pytest.raises(ValueError):
        dice.parse("banana")


def test_catalog_attacks_only_use_known_damage_types() -> None:
    for spawn in [*ENEMIES.values(), *ITEMS.values()]:
        entity = spawn.make()
        for a in getattr(entity, "available_attacks", lambda: [])():
            for roll in a.damage:
                assert roll.type in DAMAGE_TYPES, (spawn.id, roll.type)
        for key in getattr(entity, "resistances", {}):
            assert key in {"physical", "magic", *DAMAGE_TYPES}, (spawn.id, key)


# ---- enemies and the game loop -----------------------------------------------


def corridor_game(enemy: Character, gap: int) -> Game:
    """Player at x=1 facing east, enemy `gap` tiles further east in a straight corridor."""
    game = Game(RoomDirector(RandomLLM(random.Random(0)), RandomLLM(random.Random(0))), seed=0)
    game.map = MapState(name="Test", theme="cellar", tiles=["#" * 12, "#" + "." * 10 + "#", "#" * 12])
    game.map.placements = [Placement("player", 1, 1, "E"), Placement(enemy.id, 1 + gap, 1)]
    game.entities = {"player": game.player, enemy.id: enemy}
    return game


def test_enemies_walk_toward_the_player_then_attack() -> None:
    goblin = ENEMIES["goblin"].make()
    game = corridor_game(goblin, gap=4)
    enemy_turns(game.map, game.entities, game.player, AlwaysRoll(15))
    assert game.map.placement_of(goblin.id).x == 4
    enemy_turns(game.map, game.entities, game.player, AlwaysRoll(15))
    enemy_turns(game.map, game.entities, game.player, AlwaysRoll(15))
    assert game.map.placement_of(goblin.id).x == 2  # adjacent now
    assert game.player.hp == game.player.total_stats().max_hp
    enemy_turns(game.map, game.entities, game.player, AlwaysRoll(15))  # attacks
    assert game.player.hp < game.player.total_stats().max_hp


def test_walking_into_an_enemy_attacks_it_and_kills_remove_it() -> None:
    goblin = ENEMIES["goblin"].make()
    goblin.hp = 1
    game = corridor_game(goblin, gap=1)
    game.rng = AlwaysRoll(15)
    game.handle({"type": "move", "dir": "forward"})
    assert goblin.id not in game.entities
    assert game.map.placement_of(game.player.id).x == 1  # attacking doesn't move you
    assert any("falls" in line for line in game.log)


def test_player_death_ends_the_game() -> None:
    cultist = ENEMIES["cultist"].make()
    game = corridor_game(cultist, gap=1)
    game.player.hp = 1
    game.rng = AlwaysRoll(20, chance=1.0)  # everything crits, no stun procs
    game.player.attacks, game.player.inventory = [attack("Feather", "strength", ("0", "dull"))], []
    assert game.handle({"type": "attack", "attack": 0}) == "game_over"


def test_potion_heals_and_is_used_up() -> None:
    game = corridor_game(ENEMIES["goblin"].make(), gap=8)
    game.player.hp = 5
    potion = next(i for i in game.player.inventory if i.kind == "potion")
    game.handle({"type": "use_item", "itemId": potion.id})
    assert game.player.hp == 13 and potion not in game.player.inventory


def test_readying_a_weapon_makes_it_the_default_attack() -> None:
    game = corridor_game(ENEMIES["goblin"].make(), gap=8)
    hammer = ITEMS["war_hammer"].make()
    game.player.inventory.append(hammer)
    game.handle({"type": "use_item", "itemId": hammer.id})
    assert game.player.available_attacks()[0].name == "War Hammer"


def test_player_cannot_attack_friendly_npcs() -> None:
    game = corridor_game(Character(name="Hermit", stats=Stats(max_hp=8)), gap=1)
    game.handle({"type": "attack", "attack": 0})
    assert "don't want to hurt" in game.message
    assert DIR_VECTORS["E"] == (1, 0)


# ---- narration -----------------------------------------------------------------


def test_combat_events_are_collected_for_the_narrator() -> None:
    goblin = ENEMIES["goblin"].make()
    game = corridor_game(goblin, gap=1)
    game.rng = AlwaysRoll(15)
    game.handle({"type": "attack", "attack": 0})
    assert game.combat_events and any("Goblin" in e for e in game.combat_events)
    game.handle({"type": "turn", "dir": "left"})
    assert game.combat_events == []


def test_narrator_falls_back_to_raw_events_when_offline() -> None:
    from engine.llm.client import LlamaServerClient
    from engine.llm.narrator import CombatNarrator, NarrationRequest

    narrator = CombatNarrator(LlamaServerClient("http://127.0.0.1:9", timeout=1))
    text = narrator.narrate(NarrationRequest("Room", ["You hit the Goblin.", "The Goblin falls."], 10, 20))
    assert text == "You hit the Goblin. The Goblin falls."


def test_narration_worker_only_delivers_the_newest_request() -> None:
    import threading

    from engine.llm.narrator import NarrationRequest, NarrationWorker

    started, release, results = threading.Event(), threading.Event(), []

    class SlowNarrator:
        def narrate(self, request):
            started.set()
            release.wait(2)
            return request.events[0]

    worker = NarrationWorker(SlowNarrator(), lambda seq, text: results.append((seq, text)))
    worker.start()
    worker.submit(1, NarrationRequest("R", ["first"], 1, 1))
    started.wait(2)
    worker.submit(2, NarrationRequest("R", ["second"], 1, 1))  # replaces...
    worker.submit(3, NarrationRequest("R", ["third"], 1, 1))  # ...this one replaces it again
    release.set()
    for _ in range(100):
        if len(results) == 2:
            break
        threading.Event().wait(0.02)
    assert results == [(1, "first"), (3, "third")]
