"""Game state + the action handler. The UI sends actions, the Game updates itself, the server sends to_dict().

Turns: moving, attacking and drinking a potion cost a turn; after the player's turn the
player's statuses tick and every enemy acts (engine/combat/ai.py). Turning and menus are free.

Story: every room is one chapter of the campaign (engine/story). The exit stays sealed until the
chapter's objective is done; finishing the last chapter (or dying) ends the run with an epilogue.
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
from engine.story.progress import StoryProgress
from engine.world.mapgen import build_room
from engine.world.spawn import populate

log = logging.getLogger(__name__)

# ok: just send the new state. new_room: call next_room(). ending: write the epilogue (server).
# new_game: call reset() + next_room().
Outcome = Literal["ok", "new_room", "ending", "new_game"]
LOG_SIZE = 50


class Game:
    def __init__(
        self, director: RoomDirector, seed: int | None = None, debug: bool = False, start_chapter: int = 0, god: bool = False
    ):
        self.rng = random.Random(seed)
        self.seed = seed
        self.director = director
        self.debug = debug  # enables the "debug" action (engine/debug.py)
        self.start_chapter = start_chapter  # 0-based; debug runs can start later in the story
        self.start_god = god and debug  # debug: start every run in god mode
        self.reset()

    def reset(self) -> None:
        """Fresh party at the start of the story (call next_room() after)."""
        self.run = getattr(self, "run", 0) + 1  # which attempt this is; the UI shows the intro again on a new run
        self.party: list[Character] = make_party()
        self.entities: dict[str, Entity] = {}
        self.map = MapState(name="", theme="cellar", tiles=[])
        self.room_number = 0
        self.plan: RoomPlan | None = None
        self.story = StoryProgress(start_index=self.start_chapter)
        self.ending: dict | None = None  # {"kind": "victory"|"defeat", "title", "text"} once the run is over
        self.stats = {"rooms": 0, "turns": 0, "kills": 0, "damage_dealt": 0}
        self.god = self.start_god  # debug: can't die
        self.narration = ""  # the game master's latest words
        self.message = ""  # short feedback for the last action
        self.log: list[str] = []  # combat / event log, newest last
        self.log_fresh = 0  # how many log lines the last action added (UI highlights them)
        self.combat_events: list[str] = []  # what happened in combat during the last action (for the narrator)

    @property
    def player(self) -> Character:
        return self.party[0]

    # ---- rooms ---------------------------------------------------------------

    def next_room(self) -> None:
        """Ask the LLM for the current chapter's room, add what the story needs, build it, drop the player in."""
        self.room_number += 1
        self.stats["rooms"] += 1
        chapter = self.story.chapter
        ctx = RoomContext(
            self.room_number,
            self.party,
            self.map.name or None,
            chapter=chapter,
            chapter_number=self.story.number,
            chapter_count=len(self.story.campaign.chapters),
            story_so_far=self.story.finished_titles(),
        )
        self.plan = self.director.plan(ctx)
        # The story's must-haves go first so they always fit in the room.
        self.plan.enemies = [*chapter.enemies, *self.plan.enemies][: len(chapter.enemies) + chapter.max_enemies]
        self.plan.npcs = list(dict.fromkeys([*chapter.npcs, *self.plan.npcs]))
        self.plan.items = [*chapter.items, *self.plan.items]
        log.info("room %d (chapter %d) plan: %s", self.room_number, self.story.number, self.plan)

        room = build_room(self.plan.layout, self.plan.features, self.rng)
        placements, spawned = populate(self.plan, room, self.rng)
        for entity in spawned.values():
            if isinstance(entity, Character) and entity.template in chapter.dialogue:
                entity.dialogue = list(chapter.dialogue[entity.template])
        player_at = Placement(self.player.id, *room.start, facing=room.facing)

        self.map = MapState(name=self.plan.name, theme=self.plan.theme, tiles=room.tiles, placements=[player_at, *placements])
        self.entities = {self.player.id: self.player, **spawned}
        self.narration = self.plan.narration
        self.message = "(LLM offline: random room)" if self.plan.source == "fallback" else ""
        self.log_fresh = 0
        self.story.enter_room(self.plan.name, self.plan.narration)
        self._log(f"— Chapter {self.story.number}: {chapter.title} — {self.plan.name} —")
        self._log(f"Goal: {chapter.objective.text}.")
        movement.update_animations(self.map, self.entities, self.player.id)

    # ---- actions -------------------------------------------------------------

    def handle(self, action: dict) -> Outcome:
        """Apply one UI action and say what the caller (server) should do next."""
        self.message = ""
        self.log_fresh = 0
        self.combat_events = []
        if action.get("type") == "new_game":
            return "new_game"
        if self.ending:
            return "ok"  # the run is over; only new_game does anything
        took_turn = False
        match action.get("type"):
            case "move":
                result = movement.step(self.map, self.entities, self.player.id, forward=action.get("dir") != "back")
                match result.outcome:
                    case "exit":
                        return self._try_exit()
                    case "wall":
                        self.message = "A wall blocks your way."  # not logged: holding a key into a wall would spam the log
                    case "bump" if isinstance(result.entity, Character) and result.entity.hostile:
                        took_turn = self._attack(result.entity, self.player.available_attacks()[0])  # walking into an enemy attacks it
                    case "bump" if isinstance(result.entity, Character):
                        self._talk(result.entity)
                    case "pickup" if isinstance(result.entity, Item):
                        self.player.inventory.append(result.entity)
                        self._say(f"You pick up the {result.entity.name}.")
                        took_turn = True
                    case "moved":
                        p = self.map.placement_of(self.player.id)
                        log.debug("player moved to %s,%s", p.x, p.y)
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
            case "debug" if self.debug:
                from engine.debug import run_debug_command

                outcome = run_debug_command(self, action)
                if outcome != "ok":
                    return outcome
            case "option":
                self._say(f"{action.get('option')}: not implemented yet.")
            case other:
                log.warning("unknown action %r", other)

        if took_turn:
            self._world_turn()
        movement.update_animations(self.map, self.entities, self.player.id)
        return self._after_action()

    def _after_action(self) -> Outcome:
        if not self.player.is_alive:
            self.finish("defeat")
            return "ending"
        if self.story.check(self):
            self._say(f"✓ Objective complete: {self.story.chapter.objective.text}.")
            if self.story.is_last:
                self.finish("victory")
                return "ending"
            if self.story.chapter.objective.kind != "reach_exit":
                self._say("The way onward is open.")
        return "ok"

    def _try_exit(self) -> Outcome:
        if not self.story.exit_open():
            self._say(f"The way is sealed. {self.story.chapter.objective.text}.")
            return "ok"
        if self.story.is_last:  # a campaign whose last chapter is "reach the exit"
            self.finish("victory")
            return "ending"
        self.story.advance()
        return "new_room"

    def _talk(self, npc: Character) -> None:
        line = self.rng.choice(npc.dialogue) if npc.dialogue else "..."
        if npc.template in self.story.chapter.dialogue:
            # Story NPCs say their lines in order, so the player hears the whole story.
            heard = sum(1 for t in self.story.talked_to if t.startswith(f"{npc.template}#"))
            lines = self.story.chapter.dialogue[npc.template]
            line = lines[min(heard, len(lines) - 1)]
            self.story.talked(f"{npc.template}#{heard}")
        self.story.talked(npc.template)
        self._say(f'{npc.name}: "{line}"')
        self.story.note(f'{npc.name}: "{line}"')

    def finish(self, kind: Literal["victory", "defeat"]) -> None:
        """End the run. The epilogue text is written afterwards by the server (LLM, engine/llm/narrator.py)."""
        self.ending = {"kind": kind, "title": "Victory" if kind == "victory" else "Defeat", "text": ""}
        self._say("The Deep One sleeps on. You have won." if kind == "victory" else "You have fallen.")

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
        self.combat_events += result.messages
        self.stats["damage_dealt"] += result.damage
        if result.killed:
            self.stats["kills"] += 1
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
        self.stats["turns"] += 1
        hostiles_before = self._hostile_count()
        messages, _ = tick_statuses(self.player)
        messages += ai.enemy_turns(self.map, self.entities, self.player, self.rng)
        self.stats["kills"] += hostiles_before - self._hostile_count()  # killed by burning / bleeding
        self.combat_events += messages
        for line in messages:
            self._say(line)
        if self.god:
            self.player.hp = self.player.total_stats().max_hp
            self.player.statuses = []

    def _hostile_count(self) -> int:
        return sum(1 for e in self.entities.values() if isinstance(e, Character) and e.hostile)

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
        p = self.map.placement_of(self.player.id)
        return {
            "party": to_json(self.party),
            "entities": to_json(self.entities),
            "map": to_json(self.map),
            "room": self.room_number,
            "run": self.run,
            "log": self.log,
            "log_fresh": self.log_fresh,
            "damage_types": damage_type_info(),
            "story": self.story.to_dict(),
            "ending": self.ending,
            "stats": self.stats,
            "debug": {
                "god": self.god,
                "llm_rooms": self.director.use_llm,
                "room_source": self.plan.source if self.plan else None,
                "seed": self.seed,
                "player": [p.x, p.y, p.facing] if p else None,
            }
            if self.debug
            else None,
        }
