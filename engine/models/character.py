from dataclasses import dataclass, field

from engine.combat.attacks import UNARMED, Attack
from engine.combat.damage import DAMAGE_TYPES
from engine.combat.status import StatusEffect
from engine.models.entity import Entity, to_json
from engine.models.item import Item, Weapon
from engine.models.stats import Stats


@dataclass(kw_only=True)
class Character(Entity):
    """An NPC or an enemy. They are the same thing; `hostile` tells them apart."""

    hostile: bool = False
    dialogue: list[str] = field(default_factory=list)
    inventory: list[Item] = field(default_factory=list)
    hp: int | None = None  # current hp; None means start at full
    attacks: list[Attack] = field(default_factory=list)  # natural attacks and spells (weapons come from inventory)
    # Damage multipliers by damage type id or category id: {"physical": 0.5, "fire": 2.0}. See combat/damage.py.
    resistances: dict[str, float] = field(default_factory=dict)
    statuses: list[StatusEffect] = field(default_factory=list)

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

    def heal(self, amount: int) -> int:
        """Heal up to max hp. Returns how much was actually healed."""
        before = self.hp
        self.hp = min(self.total_stats().max_hp, self.hp + amount)
        return self.hp - before

    # ---- combat --------------------------------------------------------------

    def available_attacks(self) -> list[Attack]:
        """Weapons carried (first = default), then natural attacks/spells. Fists if nothing else."""
        weapons = [i.attack for i in self.inventory if isinstance(i, Weapon)]
        return [*weapons, *self.attacks] or [UNARMED]

    def armor_class(self) -> int:
        return 10 + Stats.modifier(self.total_stats().dexterity) - sum(s.ac_penalty for s in self.statuses)

    def has_status(self, status_id: str) -> bool:
        return any(s.id == status_id for s in self.statuses)

    def add_status(self, effect: StatusEffect) -> None:
        """Adding a status the character already has refreshes its duration."""
        self.remove_status(effect.id)
        self.statuses.append(effect)

    def remove_status(self, status_id: str) -> None:
        self.statuses = [s for s in self.statuses if s.id != status_id]

    def to_dict(self) -> dict:
        # Things the UI shows but can't compute itself.
        return {
            **super().to_dict(),
            "total_stats": to_json(self.total_stats()),
            "armor_class": self.armor_class(),
            "available_attacks": to_json(self.available_attacks()),
            # Final multiplier per damage type after all rules (category lookup, piercing, ...).
            "damage_multipliers": {t.id: t.multiplier(self) for t in DAMAGE_TYPES.values()},
        }
