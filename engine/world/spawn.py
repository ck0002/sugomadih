"""Turns a RoomPlan into real entities standing on free tiles of a built room."""

import random

from engine.data.catalog import ENEMIES, ITEMS, NPCS, Spawnable
from engine.llm.room_director import RoomPlan
from engine.models import Entity, Placement
from engine.world.mapgen import BuiltRoom

# Minimum walking distance from the start, so nothing spawns in your face.
MIN_DISTANCE = {"enemy": 4, "npc": 3, "item": 2}


def populate(plan: RoomPlan, room: BuiltRoom, rng: random.Random) -> tuple[list[Placement], dict[str, Entity]]:
    placements: list[Placement] = []
    entities: dict[str, Entity] = {}
    taken: set[tuple[int, int]] = set()
    distance = dict(room.spawn_cells)

    def place(ids: list[str], catalog: dict[str, Spawnable], min_distance: int) -> None:
        for spawn_id in ids:
            free = [c for c, d in room.spawn_cells if c not in taken]
            far_enough = [c for c in free if distance[c] >= min_distance]
            options = far_enough or free
            if not options:
                return  # room is full
            x, y = rng.choice(options)
            taken.add((x, y))
            entity = catalog[spawn_id].make()
            entities[entity.id] = entity
            placements.append(Placement(entity.id, x, y))

    place(plan.enemies, ENEMIES, MIN_DISTANCE["enemy"])
    place(plan.npcs, NPCS, MIN_DISTANCE["npc"])
    place(plan.items, ITEMS, MIN_DISTANCE["item"])
    return placements, entities
