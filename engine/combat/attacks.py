"""Attacks: what a weapon, spell or claw does. Plain data (damage types are referenced by id)."""

from dataclasses import dataclass, field


@dataclass
class DamageRoll:
    dice: str  # "1d6", "2d4+1"
    type: str  # DamageType id, e.g. "sharp", "fire"


@dataclass
class Attack:
    name: str
    damage: list[DamageRoll] = field(default_factory=list)  # several rolls = mixed damage (sharp + fire)
    stat: str = "strength"  # ability that adds to hit and damage: strength / dexterity / intelligence / wisdom


def attack(name: str, stat: str, *rolls: tuple[str, str]) -> Attack:
    """Shorthand: attack("Flaming Sword", "strength", ("1d6", "sharp"), ("1d4", "fire"))."""
    return Attack(name, [DamageRoll(dice, type_) for dice, type_ in rolls], stat)


UNARMED = attack("Fists", "strength", ("1d2", "dull"))
