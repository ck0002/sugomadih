"""The LLM as storyteller during play: turns dry combat log lines into a sentence or two of story.

Python decides what happened (engine/combat); the narrator only retells it. If the LLM is
offline or returns junk, the narration is just the event lines themselves.
"""

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass

from engine.llm.client import LLMClient, LLMError
from engine.llm.text import clean_story

log = logging.getLogger(__name__)

MAX_NARRATION = 240

SYSTEM_PROMPT = (
    "You are the game master of a dark fantasy dungeon crawler, narrating a fight as it happens. "
    "Retell the events you are given as one or two vivid sentences in second person ('you'). "
    "Only describe the events listed; never invent hits, misses, deaths or numbers. Answer only with JSON."
)

SCHEMA = {
    "type": "object",
    "properties": {"narration": {"type": "string", "maxLength": MAX_NARRATION, "examples": [""]}},
    "required": ["narration"],
}


@dataclass
class NarrationRequest:
    room: str
    events: list[str]  # log lines from one player action (attacks, statuses, deaths)
    player_hp: int
    player_max_hp: int


def fallback_text(request: NarrationRequest) -> str:
    return " ".join(request.events)


class CombatNarrator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def narrate(self, request: NarrationRequest) -> str:
        prompt = "\n".join(
            [
                f"Room: {request.room}. Your hp: {request.player_hp}/{request.player_max_hp}.",
                "Events this turn:",
                *(f"- {e}" for e in request.events),
            ]
        )
        try:
            reply = self.llm.complete_json(SYSTEM_PROMPT, prompt, SCHEMA, max_tokens=120)
        except LLMError as e:
            log.warning("narrator offline, using raw events: %s", e)
            return fallback_text(request)
        return clean_story(reply.get("narration"), MAX_NARRATION) or fallback_text(request)


class NarrationWorker(threading.Thread):
    """Runs narration off the main thread. Only the newest request matters: older pending ones are dropped.

    on_done(seq, text) is called from the worker thread; the caller decides if seq is still current.
    """

    def __init__(self, narrator: CombatNarrator, on_done: Callable[[int, str], None]):
        super().__init__(daemon=True, name="narrator")
        self.narrator = narrator
        self.on_done = on_done
        self._cv = threading.Condition()
        self._job: tuple[int, NarrationRequest] | None = None

    def submit(self, seq: int, request: NarrationRequest) -> None:
        with self._cv:
            self._job = (seq, request)
            self._cv.notify()

    def run(self) -> None:
        while True:
            with self._cv:
                while self._job is None:
                    self._cv.wait()
                seq, request = self._job
                self._job = None
            try:
                self.on_done(seq, self.narrator.narrate(request))
            except Exception:  # never kill the worker
                log.exception("narration failed")
