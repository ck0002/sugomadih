import random

import pytest

from engine.data.catalog import spawnable
from engine.debug import run_debug_command
from engine.game import Game
from engine.llm.client import LlamaServerClient, RandomLLM
from engine.llm.narrator import EpilogueRequest, write_epilogue
from engine.llm.room_director import RoomDirector, room_schema
from engine.models import Character, Placement
from engine.story.campaign import CAMPAIGN, chapter_index
from tests.test_engine import actions_to_exit


def make_game(seed: int = 0, chapter: int = 0, debug: bool = False) -> Game:
    rng = random.Random(seed)
    game = Game(RoomDirector(RandomLLM(rng), fallback=RandomLLM(rng)), seed=seed, debug=debug, start_chapter=chapter)
    game.next_room()
    return game


def templates(game: Game) -> list[str]:
    return [e.template for e in game.entities.values()]


def walk_to_exit(game: Game) -> str:
    game.map.placements = [p for p in game.map.placements if p.id == game.player.id]  # nothing in the way
    for action in actions_to_exit(game):
        outcome = game.handle(action)
        if outcome != "ok":
            return outcome
    return "ok"


# ---- campaign shape ------------------------------------------------------------


def test_campaign_ends_with_a_boss_fight() -> None:
    last = CAMPAIGN.chapters[-1]
    assert last.objective.kind == "defeat_boss"
    assert last.objective.target in last.enemies


@pytest.mark.parametrize("index", range(len(CAMPAIGN.chapters)))
def test_every_chapter_room_contains_what_its_story_needs(index: int) -> None:
    game = make_game(seed=index, chapter=index)
    chapter = CAMPAIGN.chapters[index]
    present = templates(game)
    for needed in [*chapter.enemies, *chapter.npcs, *chapter.items]:
        assert needed in present, (chapter.id, needed)
    assert game.map.theme in chapter.themes
    assert room_schema(chapter)["properties"]["theme"]["enum"] == list(chapter.themes)


def test_chapter_index_parsing() -> None:
    assert chapter_index("1") == 0
    assert chapter_index(3) == 2
    assert chapter_index("end") == len(CAMPAIGN.chapters) - 1
    assert chapter_index(99) == len(CAMPAIGN.chapters) - 1


# ---- objectives ----------------------------------------------------------------


def test_reach_exit_chapter_advances_the_story() -> None:
    game = make_game()
    assert walk_to_exit(game) == "new_room"
    assert game.story.number == 2


def test_sealed_exit_until_the_key_is_found() -> None:
    game = make_game(chapter=chapter_index(2))  # The Sealed Crypt
    key = next(e for e in game.entities.values() if e.template == "brass_key")
    assert walk_to_exit(game) == "ok"  # sealed
    assert "sealed" in game.message
    game.player.inventory.append(key)
    game.entities.pop(key.id)
    game.handle({"type": "turn", "dir": "left"})  # any action re-checks the objective
    assert game.story.objective_done
    assert walk_to_exit(game) == "new_room"


def test_talking_to_the_hermit_tells_the_story_in_order() -> None:
    game = make_game(chapter=chapter_index(3))
    hermit = next(e for e in game.entities.values() if e.template == "hermit")
    lines = CAMPAIGN.chapters[2].dialogue["hermit"]
    for expected in lines:
        game._talk(hermit)
        assert expected in game.message
    game.handle({"type": "turn", "dir": "left"})
    assert game.story.objective_done


def test_defeat_all_opens_the_way() -> None:
    game = make_game(chapter=chapter_index(5), debug=True)
    assert not game.story.exit_open()
    game.handle({"type": "debug", "command": "kill_all"})
    assert game.story.objective_done and game.story.exit_open()


def test_killing_the_boss_wins_the_game() -> None:
    game = make_game(chapter=chapter_index("end"))
    boss = next(e for e in game.entities.values() if e.template == "deep_priest")
    # Put the boss right in front of the player with 1 hp and make every roll hit.
    p = game.map.placement_of(game.player.id)
    game.map.placements = [pl for pl in game.map.placements if pl.id != boss.id] + [Placement(boss.id, p.x + 1, p.y)]
    p.facing = "E"
    game.map.tiles[p.y] = game.map.tiles[p.y][: p.x + 1] + "." + game.map.tiles[p.y][p.x + 2 :]
    boss.hp = 1
    game.rng = type("R", (random.Random,), {"randint": lambda self, a, b: b, "random": lambda self: 0.99})(0)
    assert game.handle({"type": "attack", "attack": 0}) == "ending"
    assert game.ending["kind"] == "victory"
    assert game.handle({"type": "move", "dir": "forward"}) == "ok"  # nothing happens after the end
    assert game.handle({"type": "new_game"}) == "new_game"


def test_epilogue_falls_back_when_offline() -> None:
    request = EpilogueRequest(True, CAMPAIGN.premise, ["A"], "B", {"rooms": 1}, fallback="The end.")
    assert write_epilogue(LlamaServerClient("http://127.0.0.1:9", timeout=1), request) == "The end."


# ---- debug ---------------------------------------------------------------------


def test_debug_commands_are_ignored_without_debug_mode() -> None:
    game = make_game(debug=False)
    assert game.handle({"type": "debug", "command": "win"}) == "ok"
    assert game.ending is None


def test_debug_teleport_to_the_end_and_win() -> None:
    game = make_game(debug=True)
    assert game.handle({"type": "debug", "command": "goto_chapter", "chapter": "end"}) == "new_room"
    game.next_room()
    assert game.story.is_last and "deep_priest" in templates(game)
    assert game.handle({"type": "debug", "command": "complete"}) == "ending"
    assert game.ending["kind"] == "victory"


def test_debug_god_mode_and_tools() -> None:
    game = make_game(debug=True, chapter=chapter_index(5))
    run_debug_command(game, {"command": "god"})
    game.player.hp = 1
    game.handle({"type": "move", "dir": "forward"})
    assert game.player.hp == game.player.total_stats().max_hp
    run_debug_command(game, {"command": "give_weapons"})
    assert len(game.player.available_attacks()) >= 5
    run_debug_command(game, {"command": "llm_rooms"})
    assert game.director.use_llm is False
    assert game.to_dict()["debug"]["god"] is True


def test_state_carries_story_and_ending() -> None:
    import json

    game = make_game()
    state = json.loads(json.dumps(game.to_dict()))
    assert state["story"]["chapter"] == 1
    assert [c["status"] for c in state["story"]["chapters"]][:2] == ["current", "locked"]
    assert state["story"]["journal"]
    assert state["ending"] is None and state["debug"] is None
    assert spawnable("deep_priest").spawn().template == "deep_priest"
    assert isinstance(spawnable("hermit").spawn(), Character)
