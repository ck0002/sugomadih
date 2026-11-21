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

## Layout (planned)

- `engine/`: Python game logic
  - `models/`: game objects as dataclasses (`Entity`, `Player`, `Enemy`, `Item`, `Weapon`, `Room`, `Encounter`, ...)
  - `data/`: content definitions (enemy and item catalogs)
  - `rules/`: dice, combat, checks, loot
  - `llm/`: prompt building, the option list sent to the LLM, response schema and parsing
  - `server.py`: bridge to the UI (JSON over stdio or a local socket)
- `ui/`: React + Ink app in TypeScript (Ink 8, React 19). Run with `cd ui && npm run dev`; typecheck with `npm run typecheck`.
  - `src/types.ts`: TS mirror of the Python models. Keep it in sync with `engine/models`.
  - `src/App.tsx`: screen layout. The top 3/4 is the world (first-person 3D view, plus minimap and Nearby panels) and the bottom 1/4 is the menu. Keys: w/s step, a/d turn 90°, ←/→ tabs, ↑/↓ select, enter use, q quit.
  - `src/view3d/raycast.ts`: pure ASCII raycaster (grid in, `Cell[][]` out). Walls are `#` and `+`, water `~` is drawn on the floor, and entities are billboard sprites scaled from their `art`.
  - Movement is on the grid: positions are whole tiles, and facing is N/E/S/W (`Placement.facing`). The Python side should use the same model.
  - `src/mock/engine.ts`: temporary stand-in for the Python rules (walking, collision). Delete it once the bridge exists.
  - `src/components/`: reusable pieces (`Panel` box, `SelectList`, `StatBlock`, `HpBar`)
  - `src/menu/tabs/`: one file per menu tab, registered in `tabs/index.ts`. To add a tab, create a file and add it to `TABS`.
  - To add a box, put another `<Panel>` into the layout in `App.tsx`.
  - `src/mock/state.ts`: fake game state used until the Python bridge exists
- `main.py`: entry point

## LLM

- Model: Qwen3.5 2B (`unsloth/Qwen3.5-2B-GGUF:Q4_K_M`, ~1.3 GB), served by llama.cpp. Start it with `./scripts/llm-server.sh`; the first run downloads the model from Hugging Face.
- OpenAI-compatible API at `http://127.0.0.1:8080/v1/chat/completions`. Thinking is turned off in the script.
- Always send `response_format: {type: "json_schema", ...}` and put the valid `choice_id`s in an `enum`, so the model can only answer with a real option. A response takes about 1.5 s (~50 tok/s on an M-series Mac).

## Conventions

- Python 3.14, managed with `uv` (`uv run main.py`, `uv add <pkg>`).
- Game objects are plain dataclasses with type hints, serializable to JSON for both the LLM and the UI.
- LLM I/O is strict JSON, e.g. `{"choice_id": "goblin_01", "narration": "..."}`. Keep a schema and validate every response.
- Keep prompts short. The model is small, so give it a few clear options, not open-ended freedom.
- Logic should be deterministic and testable without the LLM. Put the LLM behind an interface so it can be mocked.
- ASCII art: monospace only, keep it within about 80 columns, and store art as data in Python or the UI rather than hard-coding it inline.

## Hackathon mode

Move fast and keep it simple. Get a playable loop working first (explore → encounter → fight or loot → narrate), then polish.
