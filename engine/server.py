"""Bridge to the Ink UI: JSON lines over stdin/stdout.

UI -> engine:  {"type": "action", "action": {...}}            (see Action in ui/src/types.ts)
engine -> UI:  {"type": "loading", "message": str}            the LLM is working
               {"type": "state", "state": GameState, "narration": str, "message": str}
               {"type": "narrating"}                         combat happened; the LLM is retelling it
               {"type": "narration", "text": str}           the retelling (arrives later, from a worker thread)
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
import threading

from engine.game import Game
from engine.llm.client import LlamaServerClient, RandomLLM
from engine.llm.narrator import CombatNarrator, NarrationRequest, NarrationWorker
from engine.llm.room_director import RoomDirector

log = logging.getLogger("engine.server")

_stdout_lock = threading.Lock()  # the narrator thread writes too


def send(message: dict) -> None:
    line = json.dumps(message, ensure_ascii=False) + "\n"
    with _stdout_lock:
        sys.stdout.write(line)
        sys.stdout.flush()


class Narration:
    """Hands combat events to the narrator thread; only the newest narration is shown."""

    def __init__(self, game: Game, narrator: CombatNarrator):
        self.game = game
        self.seq = 0
        self.lock = threading.Lock()
        self.worker = NarrationWorker(narrator, self._done)
        self.worker.start()

    def after_action(self) -> None:
        if not self.game.combat_events:
            return
        with self.lock:
            self.seq += 1
            seq = self.seq
        p = self.game.player
        self.worker.submit(seq, NarrationRequest(self.game.map.name, list(self.game.combat_events), p.hp, p.total_stats().max_hp))
        send({"type": "narrating"})

    def invalidate(self) -> None:
        """A new room: drop any narration still being written for the old one."""
        with self.lock:
            self.seq += 1

    def _done(self, seq: int, text: str) -> None:
        with self.lock:
            if seq != self.seq:
                return
            self.game.narration = text
        send({"type": "narration", "text": text})


def send_state(game: Game) -> None:
    send({"type": "state", "state": game.to_dict(), "narration": game.narration, "message": game.message})


def enter_next_room(game: Game, narration: "Narration | None" = None) -> None:
    if narration:
        narration.invalidate()
    send({"type": "loading", "message": "The game master is drawing the next room..."})
    game.next_room()
    send_state(game)


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    seed = int(os.environ["DNLLM_SEED"]) if "DNLLM_SEED" in os.environ else None
    llm = LlamaServerClient(os.environ.get("DNLLM_LLM_URL", "http://127.0.0.1:8080"))
    game = Game(RoomDirector(llm, fallback=RandomLLM(random.Random(seed))), seed=seed)
    narration = Narration(game, CombatNarrator(llm))

    enter_next_room(game, narration)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            if message.get("type") != "action":
                continue
            match game.handle(message.get("action", {})):
                case "new_room":
                    enter_next_room(game, narration)
                case "game_over":
                    send_state(game)  # show the final blow
                    game.reset()
                    enter_next_room(game, narration)
                case _:
                    send_state(game)
                    narration.after_action()
        except Exception as e:  # never die on one bad message
            log.exception("failed to handle %r", line)
            send({"type": "error", "message": str(e)})


if __name__ == "__main__":
    main()
