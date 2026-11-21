from dataclasses import dataclass, fields


@dataclass
class Stats:
    """The six D&D ability scores, plus hp.

    The same class does two jobs: an entity's base scores, and an item's
    buffs (bonuses, which can be negative). Adding two Stats sums every field.
    """

    strength: int = 0
    dexterity: int = 0
    constitution: int = 0
    intelligence: int = 0
    wisdom: int = 0
    charisma: int = 0
    max_hp: int = 0

    def __add__(self, other: "Stats") -> "Stats":
        return Stats(**{f.name: getattr(self, f.name) + getattr(other, f.name) for f in fields(self)})

    @staticmethod
    def modifier(score: int) -> int:
        """D&D ability modifier: 10 -> +0, 14 -> +2, 8 -> -1."""
        return (score - 10) // 2

    def non_zero(self) -> dict[str, int]:
        """Only the fields that are set. Handy for showing item buffs."""
        return {f.name: v for f in fields(self) if (v := getattr(self, f.name)) != 0}
