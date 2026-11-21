from dataclasses import asdict, dataclass, field
from uuid import uuid4

from engine.models.stats import Stats


def _new_id() -> str:
    return uuid4().hex[:8]


@dataclass(kw_only=True)
class Entity:
    """Base class for anything the player can interact with: NPCs, enemies, items, ..."""

    name: str
    description: str = ""
    art: str = ""  # ASCII art, how the thing looks
    stats: Stats = field(default_factory=Stats)
    id: str = field(default_factory=_new_id)

    @property
    def kind(self) -> str:
        return type(self).__name__.lower()

    def to_dict(self) -> dict:
        """JSON-ready form for the LLM and the UI."""
        return {"kind": self.kind, **asdict(self)}
