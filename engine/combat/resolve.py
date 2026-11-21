"""One attack, start to finish: to-hit roll, damage per type, resistances, on-hit effects. And status ticks.

To hit: d20 + modifier(attack stat) >= target armor class. Natural 1 always misses;
rolling the type's crit_from or higher always hits and doubles the dice.
Damage: each DamageRoll is rolled, the stat modifier is added once (to the first roll),
then each part is multiplied by the target's resistance to that type.
"""

import random
from dataclasses import dataclass, field

from engine.combat import dice
from engine.combat.attacks import Attack
from engine.combat.damage import get_damage_type
from engine.combat.text import the, verb
from engine.models import Character, Stats


@dataclass
class AttackResult:
    hit: bool
    crit: bool = False
    damage: int = 0
    parts: list[tuple[str, int]] = field(default_factory=list)  # (damage type id, amount)
    killed: bool = False
    messages: list[str] = field(default_factory=list)


def resolve_attack(attacker: Character, attack: Attack, target: Character, rng: random.Random) -> AttackResult:
    types = [get_damage_type(r.type) for r in attack.damage]
    modifier = Stats.modifier(getattr(attacker.total_stats(), attack.stat, 10))
    crit_from = min((t.crit_from for t in types), default=20)

    roll = dice.d20(rng)
    crit = roll >= crit_from
    if roll == 1 or (not crit and roll + modifier < target.armor_class()):
        return AttackResult(hit=False, messages=[f"{the(attacker, cap=True)} {verb(attacker, 'miss')} {the(target)} ({attack.name})."])

    result = AttackResult(hit=True, crit=crit)
    notes = []
    for i, (damage_roll, dtype) in enumerate(zip(attack.damage, types)):
        raw = max(0, dice.roll(damage_roll.dice, rng, crit=crit) + (modifier if i == 0 else 0))
        mult = dtype.multiplier(target)
        amount = round(raw * mult)
        result.parts.append((dtype.id, amount))
        if mult == 0:
            notes.append(f"immune to {dtype.name.lower()}")
        elif mult > 1:
            notes.append(f"weak to {dtype.name.lower()}")
        elif mult < 1:
            notes.append(f"resists {dtype.name.lower()}")
    result.damage = sum(a for _, a in result.parts)
    target.hp -= result.damage

    parts = " + ".join(f"{a} {t}" for t, a in result.parts)
    extra = (" Critical hit!" if crit else "") + (f" ({', '.join(notes)})" if notes else "")
    result.messages.append(
        f"{the(attacker, cap=True)} {verb(attacker, 'hit')} {the(target)} with {attack.name} for {parts} damage.{extra}"
    )

    if target.is_alive:
        for (type_id, amount), dtype in zip(result.parts, types):
            if amount > 0:
                result.messages += dtype.on_hit(target, amount, rng)
    else:
        result.killed = True
        result.messages.append(f"{the(target, cap=True)} {verb(target, 'fall')}." if target.id != "player" else "You fall...")
    return result


def tick_statuses(c: Character) -> tuple[list[str], bool]:
    """Start of c's turn: damage over time, durations count down. Returns (messages, skips this turn)."""
    messages: list[str] = []
    skip = any(s.skip_turn for s in c.statuses)
    for s in list(c.statuses):
        if s.damage_per_turn and s.damage_type:
            amount = round(s.damage_per_turn * get_damage_type(s.damage_type).multiplier(c))
            c.hp -= amount
            messages.append(f"{the(c, cap=True)} {verb(c, 'take')} {amount} {s.damage_type} damage from {s.name.lower()}.")
        s.turns -= 1
        if s.turns <= 0:
            c.remove_status(s.id)
    if skip and c.is_alive:
        messages.append(f"{the(c, cap=True)} {verb(c, 'reel')} and can't act.")
    return messages, skip
