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
├── main.py                   Python entry point (still a stub)
├── pyproject.toml, uv.lock   Python project (uv, Python 3.14)
├── scripts/
│   └── llm-server.sh         starts llama-server with Qwen3.5 2B on :8080
├── engine/                   Python game logic: all the rules live here
│   ├── models/               game objects (dataclasses), exported from __init__.py
│   │   ├── stats.py          Stats: 6 ability scores + max_hp; also used for item buffs; Stats + Stats sums fields
│   │   ├── entity.py         Entity base: name, description, art (animations), animation, stats, id, play(), to_dict()
│   │   ├── item.py           Item(Entity): stats = buffs to the holder, value (gold)
│   │   └── character.py      Character(Entity): NPC or enemy (hostile flag), dialogue, inventory, hp, total_stats()
│   ├── data/                 (planned) enemy/item/map catalogs
│   ├── rules/                (planned) dice, movement, combat, checks, loot
│   ├── llm/                  (planned) client for llama-server, option lists, JSON schema, parsing, fallback
│   └── server.py             (planned) bridge to the UI (JSON over stdio or a socket)
└── ui/                       React + Ink terminal UI (TypeScript, Ink 8, React 19)
    ├── package.json          npm run dev / npm run typecheck
    └── src/
        ├── index.tsx         render() in alternate screen; q quits
        ├── App.tsx           SCREEN LAYOUT + key bindings + dispatch(action). Add or move boxes here.
        ├── types.ts          TS mirror of the Python models + GameState + Action. Keep in sync with engine/models.
        ├── state.ts          read-only GameState helpers (playerPlacement, entityAt, tileAhead, directions)
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
        │   ├── raycast.ts    pure ASCII raycaster: tiles + camera + sprites -> Cell[][] (walls, floor, sprites)
        │   └── FirstPersonView.tsx  turns GameState into camera + sprites, renders the grid
        ├── map/
        │   ├── glyphs.ts     how tiles/entities look on the minimap (TILE_GLYPHS, entityGlyph, player arrows)
        │   ├── Minimap.tsx   top-down window around the player
        │   └── NearbyList.tsx  legend: glyph -> entity name
        ├── menu/             bottom 1/4 menu box
        │   ├── MenuBox.tsx   tab bar (←/→) + active tab
        │   ├── types.ts      MenuTab / TabProps
        │   └── tabs/         one file per tab; index.ts holds the TABS list
        │       ├── ItemsTab.tsx, PartyTab.tsx, OptionsTab.tsx
        │       └── index.ts
        └── mock/             TEMPORARY until the Python bridge exists
            ├── state.ts      fake GameState (party, entities, map tiles, placements)
            ├── sprites.ts    SPRITES: animation frames for every mock entity (art`` / hold() / put() helpers)
            └── engine.ts     fake rules (walking, turning, collision, hostiles next to you play "attack"). Move to engine/rules, then delete.
```

### Where to edit

| Task | File(s) |
|---|---|
| New game object type or field | `engine/models/` + mirror it in `ui/src/types.ts` |
| New menu tab | new file in `ui/src/menu/tabs/` + add it to `TABS` in `tabs/index.ts` |
| New box/window on screen | `<Panel>` in `ui/src/App.tsx` |
| New key binding | `useInput` in `ui/src/App.tsx` (menu keys live in `MenuBox` / `SelectList`) |
| New tile type | 3D look: `WALL_COLORS` / `floorCell` in `ui/src/view3d/raycast.ts`; minimap: `TILE_GLYPHS` in `ui/src/map/glyphs.ts` |
| How things look in 3D | sprite size/colour in `view3d/FirstPersonView.tsx`; the art itself is the entity's `art` field |
| New sprite or animation | `ui/src/mock/sprites.ts` (later `engine/data/`). Switch animation in Python with `entity.play("attack")` |
| Animation speed | `FPS` in `ui/src/render/animation.tsx` |
| Test content (map, enemies, items) | `ui/src/mock/state.ts` for now; later `engine/data/` |
| LLM model or server flags | `scripts/llm-server.sh` |

### Shared data model

- The map is `tiles: string[]`: `#` wall, `+` door (drawn as wall, can be walked through), `.` floor, `~` water.
- Entities stand on the map through `placements: {id, x, y, facing?}`. Positions are whole tiles, and facing is `N|E|S|W`.
- Movement is on the grid: step forward or back, turn 90°.
- Sprites: `art` is `{animationName: frames[]}`, where each frame is a multi-line ASCII string. Every entity has `idle`, and `animation` names the one playing now. The UI loops frames at 8 fps (16 frames = 2 s), and each entity starts at a different point in its loop based on its id. In 3D, spaces outside the drawing are see-through, and art is scaled by whole numbers (at most 3×) using the size of its biggest frame. Sprites are sized as if they were 0.5 tiles further away (`SPRITE_DISTANCE_BIAS`) and step down a size until they fit on screen. The field of view adapts to the view's shape (60–90°), so things up close never go off-screen.
- `party[0]` is the player. Party members travel with the player and aren't placed on the map.
- The UI sends `Action`s (`move`, `turn`, `use_item`, `inspect`, `option`) through `dispatch` in `App.tsx`. Right now the mock engine handles them; later they go to Python.

## Running

- UI: `cd ui && npm run dev` (typecheck with `npm run typecheck`)
- LLM: `./scripts/llm-server.sh`
- Python: `uv run main.py`

## LLM

- Model: Qwen3.5 2B (`unsloth/Qwen3.5-2B-GGUF:Q4_K_M`, ~1.3 GB), served by llama.cpp. The first run of the script downloads it from Hugging Face.
- OpenAI-compatible API at `http://127.0.0.1:8080/v1/chat/completions`. Thinking is turned off in the script.
- Always send `response_format: {type: "json_schema", ...}` and put the valid `choice_id`s in an `enum`, so the model can only answer with a real option. A response takes about 1.5 s (~50 tok/s on an M-series Mac).

## Conventions

- Python 3.14, managed with `uv` (`uv add <pkg>`).
- Game objects are plain dataclasses with type hints, serializable to JSON for both the LLM and the UI.
- LLM I/O is strict JSON, e.g. `{"choice_id": "goblin_01", "narration": "..."}`. Keep a schema and validate every response.
- Keep prompts short. The model is small, so give it a few clear options, not open-ended freedom.
- Logic should be deterministic and testable without the LLM. Put the LLM behind an interface so it can be mocked.
- ASCII art: monospace only, keep it within about 80 columns, and store art as data (the `art` field) rather than hard-coding it in components.
- UI: small components. Each box is a `Panel`, each menu tab is its own file, and drawing logic (like `raycast.ts`) stays plain TS, separate from React.

## Hackathon mode

Move fast and keep it simple. Get a playable loop working first (explore → encounter → fight or loot → narrate), then polish.
