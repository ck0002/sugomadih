from dataclasses import dataclass, field

from engine.combat.attacks import UNARMED, Attack
from engine.models.entity import Entity


@dataclass(kw_only=True)
class Item(Entity):
    """Something that can be picked up and carried.

    Item.stats are the buffs it gives its holder (e.g. Stats(strength=2)).
    """

    value: int = 0  # gold


@dataclass(kw_only=True)
class Weapon(Item):
    """An item you can attack with. Using it from the menu readies it (first weapon = default attack)."""

    attack: Attack = field(default_factory=lambda: UNARMED)


@dataclass(kw_only=True)
class Potion(Item):
    """Used up when drunk."""

    heal: int = 0
