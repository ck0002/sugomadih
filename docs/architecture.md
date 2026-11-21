# Architecture

DnLLM is split into a Python game engine and a TypeScript/React Ink terminal interface. The optional local LLM is a content director, not the game engine.

## Design responsibilities

The code follows three main responsibilities:

1. **Python engine — authoritative state and rules.** It owns the party, entities, map, room transitions, movement, pickups, and action handling.
2. **LLM — constrained content selection and narration.** It selects values from the catalogues supplied by Python and returns a structured room plan plus descriptive text.
3. **React Ink UI — input and presentation.** It renders the game state, displays the story and menus, and sends player actions to the Python process. It does not own the game rules.

This separation means the engine can be tested without a real model and the UI can be changed without moving game logic into TypeScript.

## High-level data flow

```text
                       room context + allowed catalogue
       ┌─────────────────────────────────────────────────────────┐
       │                                                         ▼
┌──────────────┐       JSON-lines       ┌─────────────────┐   ┌───────────────┐
│ React Ink UI │ ─────────────────────▶ │ Python engine   │──▶│ RoomDirector  │
│              │ ◀───────────────────── │ server.py       │   └───────┬───────┘
└──────────────┘      GameState         └────────┬────────┘           │
       ▲                                         │                    ▼
       │                                         │             ┌───────────────┐
       │                                         │             │ LlamaServer   │
       │                                         │             │ or RandomLLM  │
       │                                         │             └───────────────┘
       │                                         ▼
       │                                ┌──────────────────┐
       └────────────────────────────────│ Game + rules +   │
                                        │ map generation   │
                                        └──────────────────┘
```

More precisely, the Python engine asks `RoomDirector` for a `RoomPlan`, builds a map, populates it with entities, and serializes the resulting state. The UI displays that state. When the player acts, the UI sends an action message and the engine updates the state before sending the next state message.

## Process model

For normal gameplay, the UI starts the engine as a child process:

- `ui/src/bridge/useEngine.ts` spawns `uv run --quiet python -m engine.server`.
- The child process uses stdin/stdout for the JSON-lines protocol.
- The child process's stderr is redirected to `engine.log` at the repository root.
- The UI reads each line from stdout, parses the message, and updates React state.
- On UI shutdown, the child process is terminated.

`engine/server.py` reserves stdout for protocol messages and configures logging on stderr. This is important: arbitrary log output on stdout would corrupt the line-oriented message stream.

## Engine modules

| Module | Responsibility |
|---|---|
| `engine/server.py` | Process entry point and JSON-lines bridge |
| `engine/game.py` | Central game state, room transitions, action dispatch, serialization |
| `engine/models/` | Dataclasses for stats, entities, characters, items, map state, and placements |
| `engine/data/catalog.py` | Allowed spawnable enemies, NPCs, items, room themes, layouts, features, and starting party |
| `engine/data/sprites.py` | ASCII art and animation frames |
| `engine/llm/client.py` | LLM client protocol, llama-server client, random implementation, and errors |
| `engine/llm/room_director.py` | Prompt/schema generation, room-plan validation, and fallback orchestration |
| `engine/world/mapgen.py` | Tile-grid generation, reachability calculations, and exit placement |
| `engine/world/spawn.py` | Converts a validated plan into entities and map placements |
| `engine/rules/movement.py` | Turning, stepping, collision checks, pickups, and nearby-hostile animations |

## Frontend modules

| Module | Responsibility |
|---|---|
| `ui/src/index.tsx` | Ink application root and global quit key |
| `ui/src/App.tsx` | Main layout, movement key bindings, and world/side-panel composition |
| `ui/src/bridge/useEngine.ts` | Python child process, message parsing, and action dispatch |
| `ui/src/types.ts` | TypeScript mirror of the Python data model and action union |
| `ui/src/state.ts` | Read-only helpers for player placement, entities, and tiles |
| `ui/src/view3d/` | First-person ASCII raycasting and room theme colours |
| `ui/src/map/` | Minimap glyphs and nearby-entity list |
| `ui/src/menu/` | Tab navigation and Items, Party, Options panels |
| `ui/src/components/` | Reusable panels, lists, status/stat displays, and animated art |
| `ui/src/render/` | Cell grid drawing and shared animation clock |
| `ui/src/story/` | Room narration and generation-loading display |

## Engine/UI protocol

Messages are newline-delimited JSON objects. Each line is one complete message.

### UI to engine

```json
{"type":"action","action":{"type":"move","dir":"forward"}}
```

The `action` payload is described by the `Action` union in `ui/src/types.ts` and handled by `Game.handle()` in `engine/game.py`.

Supported action shapes currently declared in the UI are:

```json
{"type":"move","dir":"forward"}
{"type":"move","dir":"back"}
{"type":"turn","dir":"left"}
{"type":"turn","dir":"right"}
{"type":"use_item","itemId":"item-id"}
{"type":"inspect","entityId":"entity-id"}
{"type":"option","option":"New room"}
```

The UI also uses `option` values for Save, Load, and Quit, but Quit is handled by the UI itself; Save and Load currently receive placeholder responses from the engine.

### Engine to UI

While generating a room, the engine sends:

```json
{"type":"loading","message":"The dungeon master is drawing the next room..."}
```

After an action or room generation, it sends a state snapshot:

```json
{"type":"state","state":{},"narration":"...","message":"..."}
```

For a handled exception, it sends:

```json
{"type":"error","message":"..."}
```

The `state` object is produced by `Game.to_dict()`. The message may be empty and is used for short action feedback or notices.

## Shared data contract

The TypeScript model in `ui/src/types.ts` mirrors Python model serialization:

- `GameState`: room number, party, entity dictionary, and map.
- `Character`: entity fields, hostility, dialogue, inventory, current HP, and computed `total_stats`.
- `Item`: entity fields plus gold value.
- `MapState`: name, theme, row strings for tiles, and entity placements.
- `Placement`: entity ID, grid position, and optional facing direction.
- `Stats`: six ability scores and `max_hp`.

When adding or renaming a field, update the Python model and the TypeScript mirror together. A mismatch can cause incorrect UI assumptions even if Python itself still runs.

## Failure boundaries

- Invalid or unavailable LLM output is handled by `RoomDirector` and its fallback client.
- Invalid JSON lines or action handling failures are caught in `engine/server.py`; an error message is sent and the process continues after the exception.
- The UI ignores stdout lines that cannot be parsed as JSON protocol messages.
- The UI displays engine startup/exit errors and points developers to `engine.log`.

These mechanisms improve resilience but do not replace validation or tests when changing the protocol.
