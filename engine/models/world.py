from dataclasses import dataclass, field
from typing import Literal

Direction = Literal["N", "E", "S", "W"]

DIR_VECTORS: dict[Direction, tuple[int, int]] = {"N": (0, -1), "E": (1, 0), "S": (0, 1), "W": (-1, 0)}
TURN_RIGHT: dict[Direction, Direction] = {"N": "E", "E": "S", "S": "W", "W": "N"}
TURN_LEFT: dict[Direction, Direction] = {"N": "W", "W": "S", "S": "E", "E": "N"}

# Map tiles. Keep in sync with the UI (view3d/raycast.ts, map/glyphs.ts).
WALL = "#"
FLOOR = "."
DOOR = "+"  # drawn like a wall, but you can walk through it
WATER = "~"
EXIT = ">"  # walking into it generates the next room
BLOCKING = {WALL}


@dataclass
class Placement:
    """Where an entity stands. Whole tiles; facing only matters for the player."""

    id: str
    x: int
    y: int
    facing: Direction | None = None


@dataclass
class MapState:
    name: str
    theme: str  # look of the room, e.g. "cellar", "crypt" (UI picks colours from it)
    tiles: list[str]  # one string per row
    placements: list[Placement] = field(default_factory=list)

    def tile(self, x: int, y: int) -> str | None:
        if 0 <= y < len(self.tiles) and 0 <= x < len(self.tiles[y]):
            return self.tiles[y][x]
        return None

    def placement_at(self, x: int, y: int) -> Placement | None:
        return next((p for p in self.placements if p.x == x and p.y == y), None)

    def placement_of(self, entity_id: str) -> Placement | None:
        return next((p for p in self.placements if p.id == entity_id), None)
