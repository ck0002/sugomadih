from dataclasses import dataclass, field

from engine.models.entity import Entity
from engine.models.item import Item
from engine.models.stats import Stats


@dataclass(kw_only=True)
class Character(Entity):
    """An NPC or an enemy. They are the same thing; `hostile` tells them apart."""

    hostile: bool = False
    dialogue: list[str] = field(default_factory=list)
    inventory: list[Item] = field(default_factory=list)
    hp: int | None = None  # current hp; None means start at full

    def __post_init__(self) -> None:
        if self.hp is None:
            self.hp = self.total_stats().max_hp

    def total_stats(self) -> Stats:
        """Base stats plus the buffs from every item carried."""
        total = self.stats
        for item in self.inventory:
            total = total + item.stats
        return total

    @property
    def is_alive(self) -> bool:
        return self.hp > 0
