# DnLLM

A D&D-style game that runs in the terminal with an ASCII art style. Python handles all game logic, a small LLM narrates, and a React Ink frontend draws the UI.

## Architecture

```
Python engine  ──(choices list)──▶  small LLM  ──(structured pick + story)──▶  Python engine
      │                                                                          │
      └──────────────────── game state (JSON) ──────────▶  Ink UI (React, terminal)
```

1. **Python owns the rules.** It holds the state (player, enemies, items, rooms, dice, combat, inventory) and decides which actions are legal.
2. **The LLM only chooses and narrates.** Python sends it the current context and a list of valid options (an enemy to spawn, an item to drop, an event, an NPC reply, and so on). The LLM returns one option by ID plus narration text in a fixed format (JSON). It never invents stats or outcomes.
3. **Python validates the response.** If the reply is malformed or picks an ID that isn't in the list, retry or fall back to a random or default option. The game must never crash because of LLM output.
4. **The Ink UI only renders.** It shows the ASCII scene, the story text, stats and the action menu, and it sends the player's input back to Python. It contains no game logic.

## Project structure

**Keep this tree up to date.** When you add, move or delete a file or folder, update this section in the same change. Paths marked *(planned)* don't exist yet.

```
DnLLM/
├── CLAUDE.md                 this file
├── main.py                   Python entry point (still a stub; the UI starts engine.server itself)
├── pyproject.toml, uv.lock   Python project (uv, Python 3.14, pytest as dev dep)
├── engine.log                engine stderr while the UI runs (gitignored)
├── scripts/
│   └── llm-server.sh         starts llama-server with Qwen3.5 2B on :8080
├── tests/
│   └── test_engine.py        mapgen invariants, LLM plan parsing/fallback, walk-to-exit, pickup, JSON shape
├── engine/                   Python game logic: all the rules live here
│   ├── server.py             BRIDGE to the UI: JSON lines over stdin/stdout (protocol in its docstring)
│   ├── game.py               Game: party, entities, map, next_room() (asks LLM, builds room), handle(action), to_dict()
│   ├── models/               game objects (dataclasses), exported from __init__.py
│   │   ├── stats.py          Stats: 6 ability scores + max_hp; also used for item buffs; Stats + Stats sums fields
│   │   ├── entity.py         Entity base: name, description, art (animations), animation, stats, id, play(), to_dict(); to_json()
│   │   ├── item.py           Item(Entity): stats = buffs to the holder, value (gold)
│   │   ├── character.py      Character(Entity): NPC or enemy (hostile flag), dialogue, inventory, hp, total_stats()
│   │   └── world.py          tile chars (WALL/FLOOR/DOOR/WATER/EXIT), Direction, Placement, MapState
│   ├── data/
│   │   ├── catalog.py        EVERYTHING THE LLM CAN SPAWN: ENEMIES, NPCS, ITEMS (Spawnable id+blurb+make), THEMES, LAYOUTS, FEATURES, make_party()
│   │   └── sprites.py        ASCII animations for every entity (art/hold/put/blink helpers)
│   ├── llm/
│   │   ├── client.py         LLMClient protocol, LlamaServerClient (json_schema constrained), RandomLLM (offline/tests), LLMError
│   │   └── room_director.py  room_schema() + room_prompt() from the catalog, parse_room_plan() validation, RoomDirector (LLM -> fallback)
│   ├── world/
│   │   ├── mapgen.py         build_room(layout, features, rng): tiles, start, exit, spawn cells (all reachable, one exit)
│   │   └── spawn.py          populate(plan, room, rng): RoomPlan ids -> entities + placements on free tiles
│   └── rules/
│       ├── movement.py       step/turn, walls, bump, pick up items, reach exit, attack animation when adjacent
│       └── (planned)         dice, combat, checks, loot
└── ui/                       React + Ink terminal UI (TypeScript, Ink 8, React 19)
    ├── package.json          npm run dev / npm run typecheck
    └── src/
        ├── index.tsx         render() in alternate screen; q quits
        ├── App.tsx           SCREEN LAYOUT + key bindings. Add or move boxes here.
        ├── types.ts          TS mirror of the Python models + GameState + Action. Keep in sync with engine/models.
        ├── state.ts          read-only GameState helpers (playerPlacement, entityAt, tileAhead, directions)
        ├── bridge/
        │   └── useEngine.ts  spawns `uv run python -m engine.server`, JSON lines; returns {state, narration, message, loading, dispatch}
        ├── story/
        │   └── StoryText.tsx LLM narration for the room, spinner while the next room is generated
        ├── components/       reusable building blocks
        │   ├── Panel.tsx     bordered box with title; every window on screen is a Panel
        │   ├── SelectList.tsx  ↑/↓/enter list used by the menu tabs
        │   ├── StatBlock.tsx   stats row (or +/- buffs)
        │   ├── AnimatedArt.tsx plays an entity's current animation in a fixed-size box
        │   └── HpBar.tsx
        ├── render/
        │   ├── CellGrid.tsx  Cell type {char, color, dim} + component that draws a Cell[][]
        │   └── animation.tsx AnimationClock (global tick, FPS=8), useTick(), framesOf/frameAt/frameBox
        ├── view3d/           first-person 3D view
        │   ├── raycast.ts    pure ASCII raycaster: tiles + camera + sprites + theme -> Cell[][]
        │   ├── themes.ts     theme name (from the LLM) -> wall/door/exit/floor/water colours
        │   └── FirstPersonView.tsx  turns GameState into camera + sprites, renders the grid
        ├── map/
        │   ├── glyphs.ts     how tiles/entities look on the minimap (TILE_GLYPHS, entityGlyph, player arrows)
        │   ├── Minimap.tsx   top-down window around the player
        │   └── NearbyList.tsx  legend: glyph -> entity name
        └── menu/             bottom 1/4 menu box
            ├── MenuBox.tsx   tab bar (←/→) + active tab
            ├── types.ts      MenuTab / TabProps
            └── tabs/         one file per tab; index.ts holds the TABS list
                ├── ItemsTab.tsx, PartyTab.tsx, OptionsTab.tsx (New room / Save / Load / Quit)
                └── index.ts
```

### Where to edit

| Task | File(s) |
|---|---|
| New enemy / NPC / item the LLM can spawn | add a `Spawnable` in `engine/data/catalog.py` + its sprite in `engine/data/sprites.py` (schema, prompt and validation update automatically) |
| New room layout or feature | builder in `engine/world/mapgen.py` (`LAYOUTS` / `FEATURES`) + a blurb in `catalog.py` |
| New room theme (look) | `THEMES` in `engine/data/catalog.py` + colours in `ui/src/view3d/themes.ts` |
| What the LLM is told / asked | `SYSTEM_PROMPT`, `room_prompt()`, `room_schema()` in `engine/llm/room_director.py` |
| New player action | `Action` in `ui/src/types.ts` + `Game.handle()` in `engine/game.py` |
| Game rules | `engine/rules/` (movement is in `movement.py`) |
| New game object type or field | `engine/models/` + mirror it in `ui/src/types.ts` |
| New menu tab | new file in `ui/src/menu/tabs/` + add it to `TABS` in `tabs/index.ts` |
| New box/window on screen | `<Panel>` in `ui/src/App.tsx` |
| New key binding | `useInput` in `ui/src/App.tsx` (menu keys live in `MenuBox` / `SelectList`) |
| New tile type | `engine/models/world.py` + `SOLID`/`wallColor`/`floorCell` in `ui/src/view3d/raycast.ts` + `TILE_GLYPHS` in `ui/src/map/glyphs.ts` |
| How things look in 3D | sprite size/colour in `view3d/FirstPersonView.tsx`; the art itself is the entity's `art` field |
| Animation speed | `FPS` in `ui/src/render/animation.tsx` |
| LLM model or server flags | `scripts/llm-server.sh` |

### Shared data model

- The map is `tiles: string[]`: `#` wall, `+` door (drawn as wall, can be walked through), `.` floor, `~` water, `>` exit (walking into it makes the next room). `map.theme` picks colours.
- Entities stand on the map through `placements: {id, x, y, facing?}`. Positions are whole tiles, and facing is `N|E|S|W`.
- Movement is on the grid: step forward or back, turn 90°. Walking onto an item picks it up. Walking into a character shows a message (enemy blocks, NPC says a dialogue line).
- Sprites: `art` is `{animationName: frames[]}`, where each frame is a multi-line ASCII string. Every entity has `idle`, and `animation` names the one playing now (Python: `entity.play("attack")`). The UI loops frames at 8 fps (16 frames = 2 s), and each entity starts at a different point in its loop based on its id. In 3D, spaces outside the drawing are see-through, and art is scaled by whole numbers (at most 3×) using the size of its biggest frame. Sprites are sized as if they were 0.5 tiles further away (`SPRITE_DISTANCE_BIAS`) and step down a size until they fit on screen. The field of view adapts to the view's shape (60–90°), so things up close never go off-screen.
- `party[0]` is the player. Party members travel with the player and aren't placed on the map. Characters also carry `total_stats` (base + item buffs) for the UI.
- GameState = `{room, party, entities, map}` from `Game.to_dict()`.

### Engine <-> UI protocol (JSON lines over stdio)

- UI -> engine: `{"type": "action", "action": Action}`.
- Engine -> UI: `{"type": "loading", "message"}` while the LLM works, `{"type": "state", "state", "narration", "message"}` after every action, and `{"type": "error", "message"}`.
- The engine's stdout is only for protocol messages. Logs go to stderr, and the UI writes them to `engine.log`.

## Running

1. LLM: `./scripts/llm-server.sh` (leave it running; without it the engine falls back to random rooms)
2. Game: `cd ui && npm run dev` (the UI starts the Python engine itself)
- Engine alone (debug): `uv run python -m engine.server`, then type action JSON lines. `DNLLM_SEED=1` makes it deterministic, and `DNLLM_LLM_URL` points it at another server.
- Tests: `uv run pytest -q`. Typecheck UI: `cd ui && npm run typecheck`.

## LLM

- Model: Qwen3.5 2B (`unsloth/Qwen3.5-2B-GGUF:Q4_K_M`, ~1.3 GB), served by llama.cpp. The first run of the script downloads it from Hugging Face.
- OpenAI-compatible API at `http://127.0.0.1:8080/v1/chat/completions`. Thinking is turned off in the script.
- Room flow: `room_schema()` (enums built from the catalog) + `room_prompt()` -> LLM -> JSON `{theme, layout, features[], enemies[], npcs[], items[], name, narration}` -> `parse_room_plan()` (drops unknown ids, caps counts, trims cut-off narration) -> `build_room()` + `populate()`.
- If the server is down or the reply is unusable, `RoomDirector` uses `RandomLLM` instead (a random answer that fits the schema), and the UI shows "(LLM offline: random room)".
- A room takes about 3–4 s to generate (~50 tok/s on an M-series Mac).

## Conventions

- Python 3.14, managed with `uv` (`uv add <pkg>`).
- Game objects are plain dataclasses with type hints, serializable to JSON for both the LLM and the UI.
- LLM I/O is strict JSON, constrained by a JSON schema whose enums are the valid ids. Validate every response anyway, and never let LLM output crash the game.
- Keep prompts short. The model is small, so give it a few clear options, not open-ended freedom.
- Logic should be deterministic and testable without the LLM. Use the `LLMClient` protocol; tests use `RandomLLM`.
- ASCII art: monospace only, keep it within about 80 columns, and store art as data (the `art` field) rather than hard-coding it in components.
- UI: small components. Each box is a `Panel`, each menu tab is its own file, and drawing logic (like `raycast.ts`) stays plain TS, separate from React.

## Hackathon mode

Move fast and keep it simple. Get a playable loop working first (explore → encounter → fight or loot → narrate), then polish.
