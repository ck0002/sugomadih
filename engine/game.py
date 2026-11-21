"""Game state + the action handler. The UI sends actions, the Game updates itself, the server sends to_dict().

Turns: moving, attacking and drinking a potion cost a turn; after the player's turn the
player's statuses tick and every enemy acts (engine/combat/ai.py). Turning and menus are free.
"""

import logging
import random
from typing import Literal

from engine.combat import ai
from engine.combat.damage import damage_type_info
from engine.combat.resolve import resolve_attack, tick_statuses
from engine.data.catalog import make_party
from engine.llm.room_director import RoomContext, RoomDirector, RoomPlan
from engine.models import DIR_VECTORS, Character, Entity, Item, MapState, Placement, Potion, Weapon, to_json
from engine.rules import movement
from engine.world.mapgen import build_room
from engine.world.spawn import populate

log = logging.getLogger(__name__)

Outcome = Literal["ok", "new_room", "game_over"]
LOG_SIZE = 50


class Game:
    def __init__(self, director: RoomDirector, seed: int | None = None):
        self.rng = random.Random(seed)
        self.director = director
        self.reset()

    def reset(self) -> None:
        """Fresh party at the top of the dungeon (call next_room() after)."""
        self.party: list[Character] = make_party()
        self.entities: dict[str, Entity] = {}
        self.map = MapState(name="", theme="cellar", tiles=[])
        self.room_number = 0
        self.plan: RoomPlan | None = None
        self.narration = ""  # the LLM's story text for the current room
        self.message = ""  # short feedback for the last action
        self.log: list[str] = []  # combat / event log, newest last
        self.log_fresh = 0  # how many log lines the last action added (UI highlights them)

    @property
    def player(self) -> Character:
        return self.party[0]

    # ---- rooms ---------------------------------------------------------------

    def next_room(self) -> None:
        """Ask the LLM for the next room, build it and drop the player at its start."""
        self.room_number += 1
        ctx = RoomContext(self.room_number, self.party, self.map.name or None)
        self.plan = self.director.plan(ctx)
        log.info("room %d plan: %s", self.room_number, self.plan)

        room = build_room(self.plan.layout, self.plan.features, self.rng)
        placements, spawned = populate(self.plan, room, self.rng)
        player_at = Placement(self.player.id, *room.start, facing=room.facing)

        self.map = MapState(name=self.plan.name, theme=self.plan.theme, tiles=room.tiles, placements=[player_at, *placements])
        self.entities = {self.player.id: self.player, **spawned}
        self.narration = self.plan.narration
        self.message = "(LLM offline: random room)" if self.plan.source == "fallback" else ""
        self.log_fresh = 0
        self._log(f"— Room {self.room_number}: {self.plan.name} —")
        movement.update_animations(self.map, self.entities, self.player.id)

    # ---- actions -------------------------------------------------------------

    def handle(self, action: dict) -> Outcome:
        """Apply one UI action. "new_room": caller calls next_room(). "game_over": caller calls reset() + next_room()."""
        self.message = ""
        self.log_fresh = 0
        took_turn = False
        match action.get("type"):
            case "move":
                result = movement.step(self.map, self.entities, self.player.id, forward=action.get("dir") != "back")
                match result.outcome:
                    case "exit":
                        return "new_room"
                    case "wall":
                        self._say("A wall blocks your way.")
                    case "bump" if isinstance(result.entity, Character) and result.entity.hostile:
                        took_turn = self._attack(result.entity, self.player.available_attacks()[0])  # walking into an enemy attacks it
                    case "bump" if isinstance(result.entity, Character):
                        line = self.rng.choice(result.entity.dialogue) if result.entity.dialogue else "..."
                        self._say(f'{result.entity.name}: "{line}"')
                    case "pickup" if isinstance(result.entity, Item):
                        self.player.inventory.append(result.entity)
                        self._say(f"You pick up the {result.entity.name}.")
                        took_turn = True
                    case "moved":
                        took_turn = True
            case "turn":
                movement.turn(self.map, self.player.id, "left" if action.get("dir") == "left" else "right")
            case "attack":
                took_turn = self._attack_ahead(action.get("attack", 0))
            case "use_item":
                took_turn = self._use_item(action.get("itemId"))
            case "inspect":
                entity = self._find(action.get("entityId"))
                if entity:
                    self._say(f"{entity.name}: {entity.description}")
            case "option" if action.get("option") == "New room":
                return "new_room"
            case "option":
                self._say(f"{action.get('option')}: not implemented yet.")
            case other:
                log.warning("unknown action %r", other)

        if took_turn:
            self._world_turn()
        movement.update_animations(self.map, self.entities, self.player.id)
        if not self.player.is_alive:
            self._say("You have fallen. A new party descends into the dungeon...")
            return "game_over"
        return "ok"

    def _attack_ahead(self, attack_index: object) -> bool:
        attacks = self.player.available_attacks()
        index = attack_index if isinstance(attack_index, int) and 0 <= attack_index < len(attacks) else 0
        target = self._character_ahead()
        if target is None:
            self._say(f"You swing your {attacks[index].name} at nothing.")
            return False
        if not target.hostile:
            self._say(f"You don't want to hurt the {target.name}.")
            return False
        return self._attack(target, attacks[index])

    def _attack(self, target: Character, attack) -> bool:
        self.player.play("attack")
        result = resolve_attack(self.player, attack, target, self.rng)
        for line in result.messages:
            self._say(line)
        if result.killed:
            ai.remove(self.map, self.entities, target.id)
        return True

    def _use_item(self, item_id: object) -> bool:
        item = next((i for i in self.player.inventory if i.id == item_id), None)
        match item:
            case Potion():
                healed = self.player.heal(item.heal)
                self.player.inventory.remove(item)
                self._say(f"You drink the {item.name} and heal {healed} hp.")
                return True
            case Weapon():
                # Readying a weapon moves it to the front: it becomes the default attack (f / walking into enemies).
                self.player.inventory.remove(item)
                self.player.inventory.insert(0, item)
                self._say(f"You ready the {item.name}.")
            case Item():
                self._say(f"You turn the {item.name} over in your hands. Nothing happens.")
        return False

    def _world_turn(self) -> None:
        messages, _ = tick_statuses(self.player)
        messages += ai.enemy_turns(self.map, self.entities, self.player, self.rng)
        for line in messages:
            self._say(line)

    def _character_ahead(self) -> Character | None:
        p = self.map.placement_of(self.player.id)
        if p is None:
            return None
        dx, dy = DIR_VECTORS[p.facing or "N"]
        other = self.map.placement_at(p.x + dx, p.y + dy)
        entity = self.entities.get(other.id) if other else None
        return entity if isinstance(entity, Character) else None

    def _say(self, line: str) -> None:
        """Show as the latest message and keep it in the log."""
        self.message = line
        self._log(line)

    def _log(self, line: str) -> None:
        self.log = [*self.log, line][-LOG_SIZE:]
        self.log_fresh = min(self.log_fresh + 1, LOG_SIZE)

    def _find(self, entity_id: object) -> Entity | None:
        if not isinstance(entity_id, str):
            return None
        return self.entities.get(entity_id) or next((c for c in self.party if c.id == entity_id), None)

    # ---- output --------------------------------------------------------------

    def to_dict(self) -> dict:
        """GameState as the UI expects it (ui/src/types.ts)."""
        return {
            "party": to_json(self.party),
            "entities": to_json(self.entities),
            "map": to_json(self.map),
            "room": self.room_number,
            "log": self.log,
            "log_fresh": self.log_fresh,
            "damage_types": damage_type_info(),
        }
