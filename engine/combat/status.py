"""Status effects that damage types leave behind (burning, bleeding, ...). Plain data so they serialize to the UI."""

from dataclasses import dataclass


@dataclass
class StatusEffect:
    id: str
    name: str
    turns: int  # turns left
    damage_per_turn: int = 0
    damage_type: str | None = None  # id of the DamageType that deals the per-turn damage
    skip_turn: bool = False  # e.g. stunned
    ac_penalty: int = 0  # lowers armor class while active


def bleeding() -> StatusEffect:
    return StatusEffect("bleeding", "Bleeding", turns=3, damage_per_turn=1, damage_type="sharp")


def stunned() -> StatusEffect:
    return StatusEffect("stunned", "Stunned", turns=1, skip_turn=True)


def burning() -> StatusEffect:
    return StatusEffect("burning", "Burning", turns=2, damage_per_turn=2, damage_type="fire")


def soaked() -> StatusEffect:
    return StatusEffect("soaked", "Soaked", turns=2, ac_penalty=2)
