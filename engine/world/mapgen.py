"""Builds room tiles from the LLM's choices (layout + features). Deterministic for a given rng.

Guarantees: every walkable tile is reachable from the start, there is exactly one exit (">")
in the outer wall, and the exit is as far from the start as possible.
"""

import random
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

from engine.models.world import DOOR, EXIT, FLOOR, WALL, WATER, Direction

Grid = list[list[str]]
Cell = tuple[int, int]


@dataclass
class BuiltRoom:
    tiles: list[str]
    start: Cell
    facing: Direction
    exit: Cell
    # Reachable floor cells good for spawning things, with walking distance from the start.
    spawn_cells: list[tuple[Cell, int]]


def build_room(layout: str, features: list[str], rng: random.Random) -> BuiltRoom:
    grid = LAYOUTS.get(layout, _hall)(rng)
    for feature in features:
        FEATURES.get(feature, lambda g, r: None)(grid, rng)

    start = _pick_start(grid)
    dist = _distances(grid, start)
    # Wall off anything the player can't reach (cave pockets, rubble-cut corners).
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch != WALL and (x, y) not in dist:
                row[x] = WALL

    exit_cell, approach = _place_exit(grid, dist)
    spawn_cells = [
        (cell, d)
        for cell, d in dist.items()
        if cell not in (start, approach) and grid[cell[1]][cell[0]] == FLOOR and _open_neighbours(grid, cell) >= 5
    ]
    spawn_cells.sort(key=lambda cd: (cd[1], cd[0]))
    return BuiltRoom(tiles=["".join(r) for r in grid], start=start, facing="E", exit=exit_cell, spawn_cells=spawn_cells)


# ---- layouts -----------------------------------------------------------------


def _blank(w: int, h: int) -> Grid:
    return [[WALL] * w for _ in range(h)]


def _carve(g: Grid, x0: int, y0: int, x1: int, y1: int, ch: str = FLOOR) -> None:
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            g[y][x] = ch


def _hall(rng: random.Random) -> Grid:
    w, h = rng.randint(22, 34), rng.randint(11, 15)
    g = _blank(w, h)
    _carve(g, 1, 1, w - 2, h - 2)
    return g


def _pillared(rng: random.Random) -> Grid:
    g = _hall(rng)
    h, w = len(g), len(g[0])
    for y in range(3, h - 3, 3):
        for x in range(4, w - 4, 4):
            g[y][x] = WALL
    return g


def _cross(rng: random.Random) -> Grid:
    w, h = rng.randint(25, 35), rng.randint(13, 17)
    g = _blank(w, h)
    band = h // 3
    _carve(g, 1, band, w - 2, h - 1 - band)
    half = max(2, w // 8)
    _carve(g, w // 2 - half, 1, w // 2 + half, h - 2)
    return g


def _cave(rng: random.Random) -> Grid:
    w, h = rng.randint(26, 36), rng.randint(13, 17)
    g = _blank(w, h)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            g[y][x] = FLOOR if rng.random() < 0.58 else WALL
    for _ in range(4):  # cellular automaton smoothing
        nxt = [row[:] for row in g]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                walls = sum(g[y + dy][x + dx] == WALL for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dx or dy)
                nxt[y][x] = WALL if walls >= 5 else FLOOR
        g = nxt
    return g


def _chambers(rng: random.Random) -> Grid:
    g = _hall(rng)
    h, w = len(g), len(g[0])
    for wx in (w // 3, 2 * w // 3):
        for y in range(1, h - 1):
            g[y][wx] = WALL
        g[rng.randint(2, h - 3)][wx] = DOOR
    return g


LAYOUTS: dict[str, Callable[[random.Random], Grid]] = {
    "hall": _hall,
    "pillared": _pillared,
    "cross": _cross,
    "cave": _cave,
    "chambers": _chambers,
}

# ---- features ----------------------------------------------------------------


def _floor_cells(g: Grid) -> list[Cell]:
    return [(x, y) for y, row in enumerate(g) for x, ch in enumerate(row) if ch == FLOOR]


def _water(g: Grid, rng: random.Random) -> None:
    cells = _floor_cells(g)
    if not cells:
        return
    cx, cy = rng.choice(cells)
    rx, ry = rng.randint(2, 4), rng.randint(1, 2)
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if 0 <= y < len(g) and 0 <= x < len(g[0]) and g[y][x] == FLOOR:
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    g[y][x] = WATER


def _rubble(g: Grid, rng: random.Random) -> None:
    for x, y in rng.sample(_floor_cells(g), k=min(6, len(_floor_cells(g)))):
        g[y][x] = WALL


def _pillars(g: Grid, rng: random.Random) -> None:
    open_cells = [c for c in _floor_cells(g) if _open_neighbours(g, c) == 8]
    for x, y in rng.sample(open_cells, k=min(4, len(open_cells))):
        if _open_neighbours(g, (x, y)) == 8:  # keep pillars apart
            g[y][x] = WALL


FEATURES: dict[str, Callable[[Grid, random.Random], None]] = {
    "water": _water,
    "rubble": _rubble,
    "pillars": _pillars,
}

# ---- helpers -----------------------------------------------------------------


def _open_neighbours(g: Grid, cell: Cell) -> int:
    x, y = cell
    return sum(
        0 <= y + dy < len(g) and 0 <= x + dx < len(g[0]) and g[y + dy][x + dx] != WALL
        for dy in (-1, 0, 1)
        for dx in (-1, 0, 1)
        if dx or dy
    )


def _pick_start(g: Grid) -> Cell:
    """Leftmost floor cell, as close to the middle row as possible."""
    mid = len(g) // 2
    cells = _floor_cells(g)
    if not cells:  # degenerate cave: carve a spot
        g[mid][1] = FLOOR
        return (1, mid)
    return min(cells, key=lambda c: (c[0], abs(c[1] - mid)))


def _distances(g: Grid, start: Cell) -> dict[Cell, int]:
    """BFS walking distance over everything that isn't a wall."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in dist and 0 <= n[1] < len(g) and 0 <= n[0] < len(g[0]) and g[n[1]][n[0]] != WALL:
                dist[n] = dist[(x, y)] + 1
                queue.append(n)
    return dist


def _place_exit(g: Grid, dist: dict[Cell, int]) -> tuple[Cell, Cell]:
    """Turn the outer-wall tile next to the farthest reachable floor cell into the exit."""
    h, w = len(g), len(g[0])
    best: tuple[int, Cell, Cell] | None = None
    for (x, y), d in dist.items():
        if g[y][x] != FLOOR:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ex, ey = x + dx, y + dy
            if (ex in (0, w - 1) or ey in (0, h - 1)) and g[ey][ex] == WALL and (best is None or d > best[0]):
                best = (d, (ex, ey), (x, y))
    if best is None:  # no outer wall touches the floor (shouldn't happen); punch through on the right
        approach = max(dist, key=dist.get)
        g[approach[1]][w - 1] = EXIT
        return (w - 1, approach[1]), approach
    _, (ex, ey), approach = best
    g[ey][ex] = EXIT
    return (ex, ey), approach
