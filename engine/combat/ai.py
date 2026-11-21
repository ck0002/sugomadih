"""Enemy turns: tick statuses, attack if next to the player, otherwise walk toward them if close enough."""

import random

from engine.combat.resolve import resolve_attack, tick_statuses
from engine.models import Character, Entity, MapState, Placement
from engine.models.world import BLOCKING, EXIT

AGGRO_RANGE = 6  # tiles (walking distance as the crow flies)


def enemy_turns(map: MapState, entities: dict[str, Entity], player: Character, rng: random.Random) -> list[str]:
    messages: list[str] = []
    player_at = map.placement_of(player.id)
    if player_at is None:
        return messages

    for placement in list(map.placements):
        enemy = entities.get(placement.id)
        if not (isinstance(enemy, Character) and enemy.hostile and enemy.is_alive):
            continue
        if not player.is_alive:
            break

        status_messages, skip = tick_statuses(enemy)
        messages += status_messages
        if not enemy.is_alive:
            messages.append(f"The {enemy.name} falls.")
            remove(map, entities, enemy.id)
            continue
        if skip:
            continue

        distance = abs(placement.x - player_at.x) + abs(placement.y - player_at.y)
        if distance == 1:
            enemy.play("attack")
            result = resolve_attack(enemy, rng.choice(enemy.available_attacks()), player, rng)
            messages += result.messages
        elif distance <= AGGRO_RANGE:
            step_toward(map, placement, player_at)
    return messages


def step_toward(map: MapState, mover: Placement, goal: Placement) -> None:
    """Greedy step that shrinks the distance the most; stays put if every good step is blocked."""
    options = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        x, y = mover.x + dx, mover.y + dy
        tile = map.tile(x, y)
        if tile is None or tile in BLOCKING or tile == EXIT or map.placement_at(x, y):
            continue
        options.append((abs(x - goal.x) + abs(y - goal.y), x, y))
    current = abs(mover.x - goal.x) + abs(mover.y - goal.y)
    best = min(options, default=None)
    if best and best[0] < current:
        mover.x, mover.y = best[1], best[2]


def remove(map: MapState, entities: dict[str, Entity], entity_id: str) -> None:
    map.placements = [p for p in map.placements if p.id != entity_id]
    entities.pop(entity_id, None)
