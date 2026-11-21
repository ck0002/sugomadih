"""ASCII sprite animations: {animation_name: [frames]}.

Frames play at 8 fps in the UI and loop, so 16 frames is a 2 s loop.
Write frames with art(r\"\"\"...\"\"\") so backslashes don't need escaping,
hold() a pose for several frames, put() to change one character (blinks, glints).
"""


def art(s: str) -> str:
    """Drop the first and last newline so frames can start on their own line."""
    return s.removeprefix("\n").removesuffix("\n")


def hold(frame: str, n: int) -> list[str]:
    return [frame] * n


def put(frame: str, row: int, col: int, ch: str) -> str:
    """Copy of frame with one character replaced (pads short lines)."""
    lines = frame.split("\n")
    while len(lines) <= row:
        lines.append("")
    line = lines[row].ljust(col)
    lines[row] = line[:col] + ch + line[col + 1 :]
    return "\n".join(lines)


def blink(frame: str, row: int, *cols: int, ch: str = "-") -> str:
    for c in cols:
        frame = put(frame, row, c, ch)
    return frame


# ---- party -------------------------------------------------------------------

_player = art(r"""
 o
/|\
/ \
""")
_player_shift = art(r"""
 o
/|\
 |\
""")
PLAYER = {"idle": hold(_player, 12) + hold(_player_shift, 4)}

_brena = art(r"""
 o
<|>
/ \
""")
BRENA = {
    "idle": hold(_brena, 10)
    + hold(put(_brena, 0, 3, "♪"), 3)
    + hold(put(_brena, 0, 4, "♫"), 3)
    + hold(put(_brena, 0, 3, "♪"), 2)
    + hold(_brena, 2)
}

# ---- enemies -----------------------------------------------------------------

_goblin = art(r"""
 ,   ,
(o\_/o)
 \ ^ /
/|===|\
 /   \
""")
_goblin_raise = art(r"""
 ,   ,   |
(o\_/o)  |
 \ ^ / __+
/|===|/
 /   \
""")
_goblin_snarl = art(r"""
 ,   , \
(>\_/<) \
 \ O /   +
/|===|--'
 /   \
""")
_goblin_stab = art(r"""
 ,   ,
(>\_/<)
 \ O /
/|===|---+--
 /   \
""")
GOBLIN = {
    "idle": hold(_goblin, 8)
    + hold(blink(_goblin, 0, 1, 5, ch="."), 2)
    + hold(_goblin, 6)
    + hold(blink(_goblin, 1, 1, 5), 2)
    + hold(_goblin, 2),
    "attack": hold(_goblin, 2) + hold(_goblin_raise, 4) + hold(_goblin_snarl, 2) + hold(_goblin_stab, 5) + hold(_goblin, 2),
}

_skeleton = art(r"""
  .-.
 (o.o)
  |=|
 /|#|\
  / \
""")
_skeleton_raise = art(r"""
  .-.   o
 (o.o) /
  |=| /
 /|#|/
  / \
""")
_skeleton_swing = art(r"""
  .-.
 (>.<)
  |=|___
 /|#|---o
  / \
""")
SKELETON = {
    "idle": hold(_skeleton, 12) + hold(blink(_skeleton, 1, 2, 4), 2) + hold(put(_skeleton, 2, 3, "-"), 2),
    "attack": hold(_skeleton, 2) + hold(_skeleton_raise, 5) + hold(_skeleton_swing, 6) + hold(_skeleton, 3),
}

_rat = art(r"""
  _ _
 (o.o)___
  > ^ <  )~
   '---'
""")
GIANT_RAT = {
    "idle": hold(_rat, 6)
    + hold(blink(_rat, 2, 2, 6, ch="="), 2)
    + hold(_rat, 4)
    + hold(put(_rat, 2, 10, "-"), 2)
    + hold(blink(_rat, 1, 2, 4), 2),
    "attack": hold(put(put(_rat, 1, 3, "O"), 2, 4, "W"), 4) + hold(_rat, 4),
}

_slime = art(r"""

   .--.
  /o  o\
 (  __  )
  '----'
""")
_slime_wide = art(r"""

  .----.
 / o  o \
(   __   )
 '------'
""")
_slime_tall = art(r"""
   .--.
  /    \
  |o  o|
 (  __  )
  '----'
""")
SLIME = {
    "idle": hold(_slime, 6) + hold(_slime_wide, 4) + hold(_slime, 6) + hold(_slime_tall, 4),
    "attack": hold(_slime_tall, 3) + hold(_slime_wide, 2) + hold(put(_slime_wide, 3, 5, "O"), 5) + hold(_slime, 4),
}

_cultist = art(r"""
  _/\_
 / .. \
 \ -- /
 /|  |\
/_|__|_\
""")
CULTIST = {
    "idle": hold(_cultist, 8)
    + hold(blink(_cultist, 1, 3, 4, ch="*"), 4)
    + hold(_cultist, 6)
    + hold(put(_cultist, 0, 7, "*"), 2),
    "attack": hold(blink(_cultist, 1, 3, 4, ch="*"), 4)
    + hold(put(put(_cultist, 3, 7, "~"), 3, 8, "*"), 4)
    + hold(put(put(put(_cultist, 3, 7, "~"), 3, 8, "~"), 3, 9, "*"), 4)
    + hold(_cultist, 4),
}

# ---- NPCs --------------------------------------------------------------------

_merchant = art(r"""
  ___
 (o o)
__\=/__
| [$] |
 |   |
""")


def _merchant_toss(row: int) -> str:
    return put(put(_merchant, 3, 3, " "), row, 8, "$")


MERCHANT = {
    "idle": hold(_merchant, 10)
    + hold(blink(_merchant, 1, 2, 4), 2)
    + hold(_merchant, 4)
    + [_merchant_toss(r) for r in (3, 2, 1, 0, 0, 1, 2, 3)]
}

_hermit = art(r"""
  ___
 (o o)
 (~~~)
 /| |\
  | |
""")
HERMIT = {
    "idle": hold(_hermit, 10)
    + hold(blink(_hermit, 1, 2, 4), 2)
    + hold(_hermit, 4)
    + hold(put(_hermit, 2, 2, "-"), 2)
    + hold(put(_hermit, 2, 3, "-"), 2)
}

# ---- items -------------------------------------------------------------------


def _glint(frame: str, *spots: tuple[int, int], rest: int = 10) -> dict[str, list[str]]:
    """Idle loop: the frame, then a '*' hopping over the given (row, col) spots."""
    frames = hold(frame, rest)
    for row, col in spots:
        frames += hold(put(frame, row, col, "*"), 2)
    return {"idle": frames}


SWORD = _glint(
    art(r"""
  /\
  ||
  ||
 -++-
  ||
"""),
    (0, 3),
    (1, 3),
    (2, 3),
)

_potion = art(r"""
 _
| |
/ \
\_/
""")
POTION = {"idle": hold(_potion, 10) + hold(put(_potion, 3, 1, "o"), 2) + hold(put(_potion, 2, 1, "o"), 2) + hold(put(_potion, 1, 1, "°"), 2)}

_amulet = art(r"""
 .-.
(o o)
 |=|
""")
AMULET = {"idle": hold(_amulet, 14) + hold(blink(_amulet, 1, 1, 3), 2)}

KEY = _glint(
    art(r"""
 _
(_)=+=
"""),
    (0, 3),
    (0, 5),
    (0, 6),
)

COINS = _glint(
    art(r"""
 o O
OoOo
"""),
    (0, 0),
    (0, 3),
    (1, 4),
)

_torch = art(r"""
 ()
 \/
 ||
""")
TORCH = {"idle": hold(_torch, 3) + hold(put(put(_torch, 0, 1, "{"), 0, 2, "}"), 3) + hold(_torch, 2) + hold(put(_torch, 0, 2, ")"), 2)}

HAMMER = _glint(
    art(r"""
 ___
|___|
  |
  |
  |
"""),
    (0, 1),
    (1, 2),
    (1, 3),
)

SPEAR = _glint(
    art(r"""
  ^
  |
  |
  |
  |
"""),
    (0, 2),
    (1, 3),
)

_flaming_sword = art(r"""
  /\
  ||
  ||
 -++-
  ||
""")
FLAMING_SWORD = {
    "idle": hold(put(put(_flaming_sword, 0, 1, "("), 0, 4, ")"), 3)
    + hold(put(put(_flaming_sword, 1, 1, "{"), 1, 4, "}"), 3)
    + hold(put(put(_flaming_sword, 0, 1, ")"), 0, 4, "("), 3)
    + hold(put(put(_flaming_sword, 2, 1, "("), 2, 4, ")"), 3)
}
