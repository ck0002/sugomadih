"""Tiny grammar helpers so log lines read right for the player ("you are") and others ("the Goblin is")."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.models.character import Character

PLAYER_ID = "player"


def the(c: "Character", cap: bool = False) -> str:
    text = "you" if c.id == PLAYER_ID else f"the {c.name}"
    return text[0].upper() + text[1:] if cap else text


def is_(c: "Character") -> str:
    return "are" if c.id == PLAYER_ID else "is"


def verb(c: "Character", base: str) -> str:
    """verb(player, "hit") -> "hit"; verb(goblin, "hit") -> "hits"."""
    return base if c.id == PLAYER_ID else base + ("es" if base.endswith(("s", "sh", "ch")) else "s")
