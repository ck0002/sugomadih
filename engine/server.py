"""Bridge to the Ink UI: JSON lines over stdin/stdout.

UI -> engine:  {"type": "action", "action": {...}}            (see Action in ui/src/types.ts)
engine -> UI:  {"type": "loading", "message": str}            the LLM is working
               {"type": "state", "state": GameState, "narration": str, "message": str}
               {"type": "error", "message": str}
When the player dies the engine sends the final state, then starts a new game (loading + state).

stdout is reserved for protocol messages; logs go to stderr (the UI writes them to engine.log).
Run standalone for debugging: uv run python -m engine.server
"""

import json
import logging
import os
import random
import sys

from engine.game import Game
from engine.llm.client import LlamaServerClient, RandomLLM
from engine.llm.room_director import RoomDirector

log = logging.getLogger("engine.server")


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def send_state(game: Game) -> None:
    send({"type": "state", "state": game.to_dict(), "narration": game.narration, "message": game.message})


def enter_next_room(game: Game) -> None:
    send({"type": "loading", "message": "The dungeon master is drawing the next room..."})
    game.next_room()
    send_state(game)


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    seed = int(os.environ["DNLLM_SEED"]) if "DNLLM_SEED" in os.environ else None
    llm = LlamaServerClient(os.environ.get("DNLLM_LLM_URL", "http://127.0.0.1:8080"))
    game = Game(RoomDirector(llm, fallback=RandomLLM(random.Random(seed))), seed=seed)

    enter_next_room(game)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            if message.get("type") != "action":
                continue
            match game.handle(message.get("action", {})):
                case "new_room":
                    enter_next_room(game)
                case "game_over":
                    send_state(game)  # show the final blow
                    game.reset()
                    enter_next_room(game)
                case _:
                    send_state(game)
        except Exception as e:  # never die on one bad message
            log.exception("failed to handle %r", line)
            send({"type": "error", "message": str(e)})


if __name__ == "__main__":
    main()
