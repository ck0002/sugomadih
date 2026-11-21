from dataclasses import dataclass

from engine.models.entity import Entity


@dataclass(kw_only=True)
class Item(Entity):
    """Something that can be picked up and carried.

    Item.stats are the buffs it gives its holder (e.g. Stats(strength=2)).
    """

    value: int = 0  # gold
