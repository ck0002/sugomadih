"""Dice notation: "1d6", "2d4+1", "1d8-1", "3" (flat)."""

import random
import re

_DICE = re.compile(r"^\s*(?:(\d*)d(\d+))?\s*([+-]\s*\d+)?\s*$|^\s*(\d+)\s*$")


def parse(expr: str) -> tuple[int, int, int]:
    """-> (count, sides, bonus). "1d6+2" -> (1, 6, 2); "3" -> (0, 0, 3)."""
    m = _DICE.match(expr)
    if not m:
        raise ValueError(f"bad dice expression: {expr!r}")
    if m.group(4):
        return 0, 0, int(m.group(4))
    count = int(m.group(1) or 1) if m.group(2) else 0
    sides = int(m.group(2) or 0)
    bonus = int(m.group(3).replace(" ", "")) if m.group(3) else 0
    return count, sides, bonus


def roll(expr: str, rng: random.Random, crit: bool = False) -> int:
    """Roll the dice. A crit rolls the dice twice (the bonus is added once)."""
    count, sides, bonus = parse(expr)
    if crit:
        count *= 2
    return sum(rng.randint(1, sides) for _ in range(count)) + bonus


def d20(rng: random.Random) -> int:
    return rng.randint(1, 20)
