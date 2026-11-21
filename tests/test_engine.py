import random
from collections import deque

import pytest

from engine.data.catalog import ENEMIES, ITEMS, LAYOUTS
from engine.game import Game
from engine.llm.client import LlamaServerClient, RandomLLM
from engine.llm.room_director import RoomContext, RoomDirector, parse_room_plan, room_schema
from engine.models import DIR_VECTORS, Placement
from engine.models.world import EXIT, WALL
from engine.world.mapgen import build_room


def make_game(seed: int = 0) -> Game:
    rng = random.Random(seed)
    return Game(RoomDirector(RandomLLM(rng), fallback=RandomLLM(rng)), seed=seed)


# ---- mapgen ------------------------------------------------------------------


@pytest.mark.parametrize("layout", list(LAYOUTS))
@pytest.mark.parametrize("seed", range(20))
def test_rooms_are_fully_connected_with_one_exit(layout: str, seed: int) -> None:
    room = build_room(layout, ["water", "rubble", "pillars"], random.Random(seed))
    tiles = room.tiles
    h, w = len(tiles), len(tiles[0])

    exits = [(x, y) for y, row in enumerate(tiles) for x, ch in enumerate(row) if ch == EXIT]
    assert exits == [room.exit]
    ex, ey = room.exit
    assert ex in (0, w - 1) or ey in (0, h - 1), "exit must be in the outer wall"

    # Every non-wall tile (including the exit) is reachable from the start.
    seen, queue = {room.start}, deque([room.start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[1] < h and 0 <= n[0] < w and tiles[n[1]][n[0]] != WALL:
                seen.add(n)
                queue.append(n)
    walkable = {(x, y) for y, row in enumerate(tiles) for x, ch in enumerate(row) if ch != WALL}
    assert walkable == seen


# ---- LLM plan parsing --------------------------------------------------------


def test_parse_drops_unknown_ids_and_fills_defaults() -> None:
    plan = parse_room_plan({"layout": "castle", "enemies": ["goblin", "dragon"], "npcs": ["hermit", "hermit"]})
    assert plan.layout == "hall"
    assert plan.enemies == ["goblin"]
    assert plan.npcs == ["hermit"]
    assert plan.name and plan.narration


def test_parse_survives_garbage() -> None:
    plan = parse_room_plan("not even a dict")
    assert plan.layout in LAYOUTS


def test_cut_off_narration_ends_on_a_full_sentence() -> None:
    assert parse_room_plan({"narration": "A goblin waits. Behind it, the"}).narration == "A goblin waits."


def test_schema_enums_come_from_catalog() -> None:
    props = room_schema()["properties"]
    assert props["enemies"]["items"]["enum"] == list(ENEMIES)
    assert props["items"]["items"]["enum"] == list(ITEMS)


def test_offline_llm_falls_back_to_random_room() -> None:
    director = RoomDirector(LlamaServerClient("http://127.0.0.1:9", timeout=1), fallback=RandomLLM(random.Random(1)))
    game = make_game()
    plan = director.plan(RoomContext(1, game.party))
    assert plan.source == "fallback"
    assert plan.layout in LAYOUTS


# ---- game loop ---------------------------------------------------------------


@pytest.mark.parametrize("seed", range(10))
def test_walking_to_the_exit_makes_a_new_room(seed: int) -> None:
    game = make_game(seed)
    game.next_room()
    first_room = game.map.tiles

    # Clear the path: remove everything but the player so nothing blocks the walk.
    game.map.placements = [p for p in game.map.placements if p.id == game.player.id]
    for action in actions_to_exit(game):
        if game.handle(action):
            break
    else:
        pytest.fail("never reached the exit")

    game.next_room()
    assert game.room_number == 2
    assert game.map.tiles != first_room


def test_walking_onto_an_item_picks_it_up() -> None:
    game = make_game()
    game.next_room()
    p = game.map.placement_of(game.player.id)
    dx, dy = DIR_VECTORS[p.facing]
    item = ITEMS["torch"].make()
    game.entities[item.id] = item
    game.map.placements.append(Placement(item.id, p.x + dx, p.y + dy))

    game.handle({"type": "move", "dir": "forward"})
    assert item in game.player.inventory
    assert item.id not in game.entities


def test_state_is_json_ready_for_the_ui() -> None:
    import json

    game = make_game()
    game.next_room()
    state = json.loads(json.dumps(game.to_dict()))
    assert state["party"][0]["inventory"][0]["kind"] == "item"
    assert state["map"]["placements"][0]["id"] == "player"
    assert "total_stats" in state["party"][0]


def actions_to_exit(game: Game) -> list[dict]:
    """BFS from the player to the exit, then turn/move actions to walk there."""
    tiles = game.map.tiles
    p = game.map.placement_of(game.player.id)
    target = next((x, y) for y, row in enumerate(tiles) for x, ch in enumerate(row) if ch == EXIT)
    prev: dict[tuple[int, int], tuple[int, int] | None] = {(p.x, p.y): None}
    queue = deque([(p.x, p.y)])
    while queue:
        cell = queue.popleft()
        if cell == target:
            break
        for dx, dy in DIR_VECTORS.values():
            n = (cell[0] + dx, cell[1] + dy)
            if n not in prev and 0 <= n[1] < len(tiles) and 0 <= n[0] < len(tiles[0]) and tiles[n[1]][n[0]] != WALL:
                prev[n] = cell
                queue.append(n)
    path = [target]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])
    path.reverse()

    actions, facing = [], p.facing
    order = ["N", "E", "S", "W"]
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        want = next(d for d, v in DIR_VECTORS.items() if v == (x1 - x0, y1 - y0))
        while facing != want:
            actions.append({"type": "turn", "dir": "right"})
            facing = order[(order.index(facing) + 1) % 4]
        actions.append({"type": "move", "dir": "forward"})
    return actions
