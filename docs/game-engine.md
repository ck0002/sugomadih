# Python game engine

The Python engine is the authoritative source of game state and gameplay rules. The main orchestration class is `Game` in `engine/game.py`.

## Entry point and server

Normal UI startup runs:

```bash
uv run --quiet python -m engine.server
```

`engine/server.py` creates the LLM client, a random fallback, the room director, and the `Game` instance. It generates the first room, then reads JSON messages from stdin. Each supported action is passed to `Game.handle()` and the resulting state is serialized to stdout as one JSON line.

The server reads optional environment variables:

- `DNLLM_SEED`: seed for the engine's random generator and fallback.
- `DNLLM_LLM_URL`: base URL of the local model server.

Logs go to stderr; stdout is reserved for protocol messages.

## Game lifecycle

`Game` stores:

- `rng`: the engine's random number generator;
- `director`: the room director;
- `party`: the party, where `party[0]` is the player;
- `entities`: entities currently in the room, keyed by ID;
- `map`: current room name, theme, tiles, and placements;
- `room_number`: current room index;
- `plan`: the latest room plan;
- `narration` and `message`: text shown by the UI.

### Creating a room

`Game.next_room()`:

1. Increments the room counter.
2. Builds a `RoomContext` using party state and the previous room name.
3. Requests a plan from `RoomDirector`.
4. Builds the tile map with `build_room()`.
5. Creates and places entities with `populate()`.
6. Places the player at the map start and sets the map theme/name.
7. Stores narration and a fallback notice, if applicable.
8. Updates character animations.

The caller sends a loading message before room generation and sends the new state afterwards.

## Action handling

`Game.handle(action)` currently recognises these action types:

| Action | Current engine behaviour |
|---|---|
| `move` | Calls the movement rule to step forward or backward; handles walls, characters, pickups, and exits |
| `turn` | Rotates the player left or right |
| `inspect` | Finds an entity and displays its name and description |
| `use_item` | Displays a placeholder message; no item-use effect is applied |
| `option: New room` | Requests a room transition |
| other `option` | Displays a not-implemented message |

When a movement action reaches an exit, `handle()` returns `True`; the server then calls `next_room()`. Other actions return the current state without a room transition.

## Data models

Models are dataclasses in `engine/models/`:

- **`Stats`** — strength, dexterity, constitution, intelligence, wisdom, charisma, and `max_hp`. Adding two `Stats` objects sums each field. `modifier()` calculates a D&D-style ability modifier.
- **`Entity`** — common data for entities: ID, name, description, ASCII animation frames, active animation, and base stats.
- **`Item`** — an entity with a gold value. Its `stats` represent passive stat bonuses when carried.
- **`Character`** — an entity with hostility, dialogue, inventory, and current HP. `total_stats()` adds the stats of carried items to the character's base stats.
- **`Placement`** — entity ID, x/y tile coordinates, and optional facing direction.
- **`MapState`** — room name/theme, tile rows, and entity placements.

`to_json()` and `to_dict()` convert model instances to values that can be sent through JSON.

## Map and tiles

The tile constants are declared in `engine/models/world.py`:

| Constant | Tile | Meaning |
|---|---|---|
| `WALL` | `#` | Blocking wall |
| `FLOOR` | `.` | Normal floor |
| `DOOR` | `+` | Drawn like a wall but walkable |
| `WATER` | `~` | Walkable water tile |
| `EXIT` | `>` | Room exit; walking into it requests a new room |

Only `WALL` is in the `BLOCKING` set used by movement. The visual raycaster draws doors and exits as solid-looking surfaces, even though the movement rules allow entering them (entering an exit triggers the room transition).

## Procedural map generation

`engine/world/mapgen.py` contains layout and feature builders. The current layout catalogue includes hall, pillared, cross, cave, and chambers. Feature builders include water, rubble, and pillars.

The map generator selects a start position, calculates reachable cells using breadth-first search, and places an exit at the outer wall near a far reachable floor cell. The tests assert that every non-wall tile is reachable from the start and that one exit is present.

## Entity spawning

`engine/world/spawn.py` converts the room plan's catalogue IDs into real entities. It places enemies, NPCs, and items on free spawn cells while preferring minimum distances from the player start:

- enemies: 4 tiles;
- NPCs: 3 tiles;
- items: 2 tiles.

If there are not enough cells at the preferred distance, the function can use other free cells. If the room runs out of space, further entities are skipped.

## Movement and interactions

`engine/rules/movement.py` handles grid movement:

- turning changes the player's facing direction by 90 degrees;
- stepping checks map bounds and blocking walls;
- entering an exit returns an `exit` outcome;
- walking onto an item removes it from the map and adds it to the player's inventory;
- walking into a character returns a `bump` outcome and does not move the player into that character's tile;
- hostile characters adjacent to the player can play their `attack` animation; others use `idle`.

The current bump handler displays a hostile-blocking message or one line of NPC dialogue. It does not apply damage.

## Adding a new game action

A new UI-dispatched action generally requires coordinated changes:

1. Add the action shape to the `Action` union in `ui/src/types.ts`.
2. Add handling in `Game.handle()` in `engine/game.py` or delegate to a focused rules module.
3. Add any required rule or model behaviour.
4. Connect the action to a UI input/menu component.
5. Add tests that exercise the engine result and state transition.
6. Keep `docs/gameplay.md` and this page current.
