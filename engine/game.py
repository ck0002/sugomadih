"""Game state + the action handler. The UI sends actions, the Game updates itself, the server sends to_dict()."""

import logging
import random

from engine.data.catalog import make_party
from engine.llm.room_director import RoomContext, RoomDirector, RoomPlan
from engine.models import Character, Entity, Item, MapState, Placement, to_json
from engine.rules import movement
from engine.world.mapgen import build_room
from engine.world.spawn import populate

log = logging.getLogger(__name__)


class Game:
    def __init__(self, director: RoomDirector, seed: int | None = None):
        self.rng = random.Random(seed)
        self.director = director
        self.party: list[Character] = make_party()
        self.entities: dict[str, Entity] = {}
        self.map = MapState(name="", theme="cellar", tiles=[])
        self.room_number = 0
        self.plan: RoomPlan | None = None
        self.narration = ""  # the LLM's story text for the current room
        self.message = ""  # short feedback for the last action

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
        movement.update_animations(self.map, self.entities, self.player.id)

    # ---- actions -------------------------------------------------------------

    def handle(self, action: dict) -> bool:
        """Apply one UI action. Returns True when the player reached the exit (caller then calls next_room())."""
        self.message = ""
        match action.get("type"):
            case "move":
                result = movement.step(self.map, self.entities, self.player.id, forward=action.get("dir") != "back")
                match result.outcome:
                    case "exit":
                        return True
                    case "wall":
                        self.message = "A wall blocks your way."
                    case "bump" if isinstance(result.entity, Character):
                        self.message = self._bump(result.entity)
                    case "pickup" if isinstance(result.entity, Item):
                        self.player.inventory.append(result.entity)
                        self.message = f"You pick up the {result.entity.name}."
            case "turn":
                movement.turn(self.map, self.player.id, "left" if action.get("dir") == "left" else "right")
            case "inspect":
                entity = self._find(action.get("entityId"))
                if entity:
                    self.message = f"{entity.name}: {entity.description}"
            case "use_item":
                item = next((i for i in self.player.inventory if i.id == action.get("itemId")), None)
                if item:
                    self.message = f"You turn the {item.name} over in your hands. (Using items comes later.)"
            case "option" if action.get("option") == "New room":
                return True
            case "option":
                self.message = f"{action.get('option')}: not implemented yet."
            case other:
                log.warning("unknown action %r", other)
        movement.update_animations(self.map, self.entities, self.player.id)
        return False

    def _bump(self, other: Character) -> str:
        if other.hostile:
            return f"The {other.name} blocks your way!"
        line = self.rng.choice(other.dialogue) if other.dialogue else "..."
        return f'{other.name}: "{line}"'

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
        }
