"""Grid movement: step forward/back, turn 90°, bump into things, pick up items, reach the exit."""

from dataclasses import dataclass
from typing import Literal

from engine.models import DIR_VECTORS, TURN_LEFT, TURN_RIGHT, Character, Entity, Item, MapState
from engine.models.world import BLOCKING, EXIT


@dataclass
class StepResult:
    outcome: Literal["moved", "wall", "bump", "pickup", "exit"]
    entity: Entity | None = None


def turn(map: MapState, player_id: str, direction: Literal["left", "right"]) -> None:
    p = map.placement_of(player_id)
    if p:
        p.facing = (TURN_LEFT if direction == "left" else TURN_RIGHT)[p.facing or "N"]


def step(map: MapState, entities: dict[str, Entity], player_id: str, forward: bool) -> StepResult:
    p = map.placement_of(player_id)
    if p is None:
        return StepResult("wall")
    dx, dy = DIR_VECTORS[p.facing or "N"]
    sign = 1 if forward else -1
    x, y = p.x + dx * sign, p.y + dy * sign

    tile = map.tile(x, y)
    if tile is None or tile in BLOCKING:
        return StepResult("wall")
    if tile == EXIT:
        return StepResult("exit")

    other = map.placement_at(x, y)
    if other is not None:
        entity = entities.get(other.id)
        if not isinstance(entity, Item):
            return StepResult("bump", entity)
        # Walking onto an item picks it up.
        map.placements.remove(other)
        entities.pop(other.id, None)
        p.x, p.y = x, y
        return StepResult("pickup", entity)

    p.x, p.y = x, y
    return StepResult("moved")


def update_animations(map: MapState, entities: dict[str, Entity], player_id: str) -> None:
    """Hostiles standing next to the player play "attack", everyone else "idle"."""
    player = map.placement_of(player_id)
    if player is None:
        return
    for pl in map.placements:
        entity = entities.get(pl.id)
        if entity is None or pl.id == player_id:
            continue
        adjacent = abs(pl.x - player.x) + abs(pl.y - player.y) == 1
        hostile = isinstance(entity, Character) and entity.hostile
        entity.play("attack" if hostile and adjacent else "idle")
