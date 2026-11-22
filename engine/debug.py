"""Developer commands, only accepted when the engine runs with DNLLM_DEBUG=1 (./play --debug).

UI sends {"type": "debug", "command": ..., ...}. Commands:
    goto_chapter  chapter=N (1-based; 0 = last)   build a fresh room for that chapter
    reroll                                       new room for the current chapter
    complete                                     finish the current objective (last chapter: win)
    kill_all                                     remove every hostile in the room
    heal                                         full hp, statuses cleared, for the whole party
    god                                          toggle: you can't die
    give_weapons                                 one of every weapon
    win / lose                                   jump straight to the ending
    llm_rooms                                    toggle: LLM-designed rooms vs instant random rooms
"""

from typing import TYPE_CHECKING

from engine.combat import ai
from engine.data.catalog import ITEMS
from engine.models import Character, Weapon
from engine.story.campaign import chapter_index

if TYPE_CHECKING:
    from engine.game import Game, Outcome


def run_debug_command(game: "Game", action: dict) -> "Outcome":
    command = action.get("command")
    say = game._say
    match command:
        case "goto_chapter":
            spec = action.get("chapter", 0)
            index = chapter_index("end" if spec in (0, "end") else spec)
            game.story.jump(index)
            say(f"[debug] Teleport to chapter {index + 1}: {game.story.chapter.title}")
            return "new_room"
        case "reroll":
            say("[debug] New room for this chapter")
            return "new_room"
        case "complete":
            game.story.complete()
            say(f"[debug] Objective complete: {game.story.chapter.objective.text}")
            if game.story.is_last:
                game.finish("victory")
                return "ending"
        case "kill_all":
            hostiles = [e for e in game.entities.values() if isinstance(e, Character) and e.hostile]
            for enemy in hostiles:
                ai.remove(game.map, game.entities, enemy.id)
            game.stats["kills"] += len(hostiles)
            say(f"[debug] Removed {len(hostiles)} enemies")
        case "heal":
            for member in game.party:
                member.hp = member.total_stats().max_hp
                member.statuses = []
            say("[debug] Party healed")
        case "god":
            game.god = not game.god
            say(f"[debug] God mode {'on' if game.god else 'off'}")
        case "give_weapons":
            weapons = [s.spawn() for s in ITEMS.values()]
            weapons = [w for w in weapons if isinstance(w, Weapon)]
            game.player.inventory += weapons
            say(f"[debug] Added {', '.join(w.name for w in weapons)}")
        case "win" | "lose":
            game.finish("victory" if command == "win" else "defeat")
            return "ending"
        case "llm_rooms":
            game.director.use_llm = not game.director.use_llm
            say(f"[debug] LLM rooms {'on' if game.director.use_llm else 'off (instant random rooms)'}")
        case _:
            say(f"[debug] unknown command {command!r}")
    return "ok"
