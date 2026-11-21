from dataclasses import dataclass, field, fields
from typing import Any
from uuid import uuid4

from engine.models.stats import Stats


def _new_id() -> str:
    return uuid4().hex[:8]


@dataclass(kw_only=True)
class Entity:
    """Base class for anything the player can interact with: NPCs, enemies, items, ..."""

    name: str
    description: str = ""
    # ASCII art animations: name -> frames, each frame a multi-line string.
    # Every entity should have "idle"; others ("attack", "hurt", ...) are optional.
    # The UI plays frames at a fixed fps and loops them.
    art: dict[str, list[str]] = field(default_factory=dict)
    animation: str = "idle"  # which animation is playing now
    stats: Stats = field(default_factory=Stats)
    id: str = field(default_factory=_new_id)

    @property
    def kind(self) -> str:
        return type(self).__name__.lower()

    def play(self, animation: str) -> None:
        """Switch animation; falls back to idle if this entity doesn't have it."""
        self.animation = animation if animation in self.art else "idle"

    def to_dict(self) -> dict:
        """JSON-ready form for the LLM and the UI. Nested entities (inventory) get their "kind" too."""
        return {"kind": self.kind, **{f.name: to_json(getattr(self, f.name)) for f in fields(self)}}


def to_json(value: Any) -> Any:
    """Turn models into plain JSON values. Uses to_dict() where a class has one."""
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dataclass_fields__"):
        return {f: to_json(getattr(value, f)) for f in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json(v) for v in value]
    return value
