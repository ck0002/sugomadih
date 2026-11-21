"""Damage types: an abstract class tree. Categories are abstract, the leaves are the real types.

    DamageType                 (abstract)
    ├── PhysicalDamage         (abstract) weapons and claws
    │   ├── Sharp              may cause Bleeding
    │   ├── Dull               may Stun
    │   └── Piercing           crits on 19-20, can't be resisted
    └── MagicDamage            (abstract) spells
        ├── Fire               sets Burning; dries a Soaked target instead
        └── Water              Soaks (-2 AC) and puts out Burning

Resistances are looked up along the tree: a target with {"physical": 0.5, "dull": 2.0} takes
double from Dull but half from Sharp and Piercing. 0 = immune, 0.5 = resists, 2 = weak.

To add a type: subclass a category (or DamageType for a whole new category), set the class
attributes, implement on_hit(), and decorate with @register. Then use its id in attacks.
"""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from engine.combat import status
from engine.combat.text import is_, the

if TYPE_CHECKING:
    from engine.models.character import Character

DAMAGE_TYPES: dict[str, "DamageType"] = {}


def register[T: type["DamageType"]](cls: T) -> T:
    DAMAGE_TYPES[cls.id] = cls()
    return cls


def get_damage_type(type_id: str) -> "DamageType":
    try:
        return DAMAGE_TYPES[type_id]
    except KeyError:
        raise ValueError(f"unknown damage type {type_id!r}; known: {', '.join(DAMAGE_TYPES)}") from None


class DamageType(ABC):
    id: ClassVar[str] = "damage"
    name: ClassVar[str] = "Damage"
    color: ClassVar[str] = "white"  # how the UI colours this type
    description: ClassVar[str] = ""
    crit_from: ClassVar[int] = 20  # natural d20 roll needed for a critical hit

    def lineage(self) -> list[str]:
        """Ids from this type up to the root: Sharp -> ["sharp", "physical", "damage"]."""
        return [cls.__dict__["id"] for cls in type(self).__mro__ if "id" in cls.__dict__]

    @property
    def category(self) -> str:
        lineage = self.lineage()
        return lineage[1] if len(lineage) > 1 else lineage[0]

    def multiplier(self, target: "Character") -> float:
        """Most specific resistance on the target wins; 1.0 if it has none for this type."""
        for type_id in self.lineage():
            if type_id in target.resistances:
                return target.resistances[type_id]
        return 1.0

    @abstractmethod
    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        """Side effects after this type dealt `amount` damage. Returns messages for the log."""


class PhysicalDamage(DamageType, ABC):
    id = "physical"
    name = "Physical"


class MagicDamage(DamageType, ABC):
    id = "magic"
    name = "Magic"


# ---- physical ----------------------------------------------------------------


@register
class Sharp(PhysicalDamage):
    id = "sharp"
    name = "Sharp"
    color = "white"
    description = "Blades and claws. 30% chance to cause bleeding."
    BLEED_CHANCE = 0.3

    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        if rng.random() < self.BLEED_CHANCE and not target.has_status("bleeding"):
            target.add_status(status.bleeding())
            return [f"{the(target, cap=True)} {is_(target)} bleeding."]
        return []


@register
class Dull(PhysicalDamage):
    id = "dull"
    name = "Dull"
    color = "yellow"
    description = "Clubs and hammers. 25% chance to stun for a turn."
    STUN_CHANCE = 0.25

    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        if rng.random() < self.STUN_CHANCE:
            target.add_status(status.stunned())
            return [f"{the(target, cap=True)} {is_(target)} stunned!"]
        return []


@register
class Piercing(PhysicalDamage):
    id = "piercing"
    name = "Piercing"
    color = "cyan"
    description = "Spears and arrows. Crits on 19-20 and can't be resisted."
    crit_from = 19

    def multiplier(self, target: "Character") -> float:
        return max(1.0, super().multiplier(target))  # weaknesses still count

    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        return []


# ---- magic -------------------------------------------------------------------


@register
class Fire(MagicDamage):
    id = "fire"
    name = "Fire"
    color = "red"
    description = "Sets the target on fire (2 damage a turn). Soaked targets dry off instead."

    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        if target.has_status("soaked"):
            target.remove_status("soaked")
            return [f"Steam hisses off {the(target)}."]
        target.add_status(status.burning())
        return [f"{the(target, cap=True)} {is_(target)} on fire!"]


@register
class Water(MagicDamage):
    id = "water"
    name = "Water"
    color = "blue"
    description = "Soaks the target (-2 armor class) and puts out fire."

    def on_hit(self, target: "Character", amount: int, rng: random.Random) -> list[str]:
        messages = []
        if target.has_status("burning"):
            target.remove_status("burning")
            messages.append(f"The flames on {the(target)} go out.")
        target.add_status(status.soaked())
        messages.append(f"{the(target, cap=True)} {is_(target)} soaked.")
        return messages


def damage_type_info() -> dict[str, dict]:
    """Metadata for the UI (colours, names, descriptions), keyed by id."""
    return {
        t.id: {"name": t.name, "category": t.category, "color": t.color, "description": t.description, "lineage": t.lineage()}
        for t in DAMAGE_TYPES.values()
    }
