"""Where the party is in the campaign: current chapter, whether its objective is done, the journal."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from engine.models import Character, Item
from engine.story.campaign import CAMPAIGN, Campaign, Chapter

if TYPE_CHECKING:
    from engine.game import Game


@dataclass
class JournalEntry:
    chapter: int  # 1-based
    title: str
    text: str


class StoryProgress:
    def __init__(self, campaign: Campaign = CAMPAIGN, start_index: int = 0):
        self.campaign = campaign
        self.index = start_index
        self.objective_done = False
        self.talked_to: set[str] = set()
        self.journal: list[JournalEntry] = []

    @property
    def chapter(self) -> Chapter:
        return self.campaign.chapters[self.index]

    @property
    def number(self) -> int:
        return self.index + 1

    @property
    def is_last(self) -> bool:
        return self.index == len(self.campaign.chapters) - 1

    def finished_titles(self) -> list[str]:
        return [c.title for c in self.campaign.chapters[: self.index]]

    # ---- progress ------------------------------------------------------------

    def enter_room(self, room_name: str, narration: str) -> None:
        self.objective_done = False
        self.talked_to.clear()
        self.note(f"{room_name}. {narration}")

    def note(self, text: str) -> None:
        self.journal.append(JournalEntry(self.number, self.chapter.title, text))

    def talked(self, template: str) -> None:
        self.talked_to.add(template)

    def exit_open(self) -> bool:
        return self.chapter.objective.kind == "reach_exit" or self.objective_done

    def check(self, game: "Game") -> bool:
        """Re-evaluate the objective. Returns True when it just became complete."""
        if self.objective_done:
            return False
        objective = self.chapter.objective
        match objective.kind:
            case "collect":
                done = any(isinstance(i, Item) and i.template == objective.target for i in game.player.inventory)
            case "talk":
                done = objective.target in self.talked_to
            case "defeat_all":
                done = not any(isinstance(e, Character) and e.hostile for e in game.entities.values())
            case "defeat_boss":
                done = not any(e.template == objective.target for e in game.entities.values())
            case _:
                done = False  # reach_exit is completed by walking out
        if done:
            self.objective_done = True
            self.note(f"✓ {objective.text}.")
        return done

    def complete(self) -> None:
        """Debug: mark the objective as done."""
        if not self.objective_done:
            self.objective_done = True
            self.note(f"✓ {self.chapter.objective.text} (debug).")

    def advance(self) -> None:
        self.index = min(self.index + 1, len(self.campaign.chapters) - 1)
        self.objective_done = False

    def jump(self, index: int) -> None:
        self.index = max(0, min(index, len(self.campaign.chapters) - 1))
        self.objective_done = False

    # ---- output --------------------------------------------------------------

    def to_dict(self) -> dict:
        def status(i: int) -> str:
            return "done" if i < self.index else "current" if i == self.index else "locked"

        return {
            "title": self.campaign.title,
            "chapter": self.number,
            "chapter_count": len(self.campaign.chapters),
            "chapter_title": self.chapter.title,
            "objective": {"text": self.chapter.objective.text, "kind": self.chapter.objective.kind, "done": self.objective_done},
            "exit_open": self.exit_open(),
            "chapters": [
                {"title": c.title, "objective": c.objective.text, "status": status(i)}
                for i, c in enumerate(self.campaign.chapters)
            ],
            "journal": [{"chapter": j.chapter, "title": j.title, "text": j.text} for j in self.journal],
        }
