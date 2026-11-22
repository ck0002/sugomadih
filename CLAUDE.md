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
├── setup                     FIRST-TIME SETUP: installs Homebrew (macOS) / uv / Node 22+ / llama.cpp if missing, uv sync, npm install, downloads the model. --yes, --no-model
├── play                      LAUNCHER: ./play [--offline] [--seed N] [--port P] [--check] [--debug] [--chapter N|end] [--god] [--fast]
├── DnLLM.command             double-click launcher for macOS Finder (calls ./play)
├── main.py                   launcher logic: checks tools, npm install on first run, starts/reuses llama-server, runs the UI, stops what it started
├── llm-server.log            llama-server output when the launcher started it (gitignored)
├── pyproject.toml, uv.lock   Python project (uv, Python 3.14, pytest as dev dep)
├── engine.log                engine stderr while the UI runs (gitignored)
├── .dnllm-settings.json      player settings saved by the UI (gitignored)
├── scripts/
│   └── llm-server.sh         starts llama-server with Qwen3.5 2B on :8080
├── tests/
│   ├── test_engine.py        mapgen invariants, LLM plan parsing/fallback, walk-to-exit, pickup, JSON shape
│   ├── test_combat.py        damage type tree, resistances, crits, statuses, enemy AI, death, potions
│   └── test_story.py         campaign rooms, sealed exits, every objective kind, boss victory, epilogue, debug commands
├── engine/                   Python game logic: all the rules live here
│   ├── server.py             BRIDGE to the UI: JSON lines over stdin/stdout (protocol in its docstring); runs the narrator thread
│   ├── game.py               Game: party, entities, map, story, ending, stats, next_room(), handle(action) -> ok/new_room/ending/new_game, to_dict()
│   ├── debug.py              dev commands (teleport, complete, kill_all, heal, god, give_weapons, win/lose, llm_rooms), only with DNLLM_DEBUG=1
│   ├── models/               game objects (dataclasses), exported from __init__.py
│   │   ├── stats.py          Stats: 6 ability scores + max_hp; also used for item buffs; Stats + Stats sums fields
│   │   ├── entity.py         Entity base: name, description, art (animations), animation, stats, id, play(), to_dict(); to_json()
│   │   ├── item.py           Item(Entity): stats = buffs, value; Weapon(Item): attack; Potion(Item): heal
│   │   ├── character.py      Character(Entity): hostile, dialogue, inventory, hp, attacks, resistances, statuses, available_attacks(), armor_class()
│   │   └── world.py          tile chars (WALL/FLOOR/DOOR/WATER/EXIT), Direction, Placement, MapState
│   ├── data/
│   │   ├── catalog.py        EVERYTHING THE LLM CAN SPAWN: ENEMIES, NPCS, ITEMS (Spawnable id+blurb+make/spawn), BOSSES (story only), THEMES, LAYOUTS, FEATURES, spawnable(id), make_party()
│   │   └── sprites.py        ASCII animations for every entity (art/hold/put/blink helpers)
│   ├── llm/
│   │   ├── client.py         LLMClient protocol, LlamaServerClient (json_schema constrained), RandomLLM (offline/tests), LLMError
│   │   ├── room_director.py  room_schema() + room_prompt() from the catalog, parse_room_plan() validation, RoomDirector (LLM -> fallback)
│   │   ├── narrator.py       CombatNarrator (retells a turn's combat events) + NarrationWorker thread (newest request wins); write_epilogue()
│   │   └── text.py           clean_story(): trims LLM story text to the last full sentence
│   ├── story/                THE CAMPAIGN
│   │   ├── campaign.py       CAMPAIGN "The Dreaming Deep": premise + 6 Chapters (objective, LLM guidance, themes, required spawns, NPC lines); chapter_index()
│   │   └── progress.py       StoryProgress: current chapter, objective check, sealed exit, journal, to_dict()
│   ├── combat/               FIGHTING
│   │   ├── damage.py         DamageType (abstract) -> PhysicalDamage/MagicDamage (abstract) -> Sharp, Dull, Piercing, Fire, Water; @register, DAMAGE_TYPES
│   │   ├── attacks.py        DamageRoll(dice, type id), Attack(name, damage[], stat), attack() shorthand, UNARMED
│   │   ├── status.py         StatusEffect + bleeding/stunned/burning/soaked
│   │   ├── resolve.py        resolve_attack() (to-hit, crits, damage per type, resistances, on_hit) + tick_statuses()
│   │   ├── ai.py             enemy_turns(): tick statuses, attack if adjacent, else step toward the player (AGGRO_RANGE)
│   │   ├── dice.py           "2d4+1" parsing/rolling, d20
│   │   └── text.py           log grammar helpers (you are / the Goblin is)
│   ├── world/
│   │   ├── mapgen.py         build_room(layout, features, rng): tiles, start, exit, spawn cells (all reachable, one exit)
│   │   └── spawn.py          populate(plan, room, rng): RoomPlan ids -> entities + placements on free tiles
│   └── rules/
│       ├── movement.py       step/turn, walls, bump, pick up items, reach exit, attack animation when adjacent
│       └── (planned)         dice, combat, checks, loot
└── ui/                       React + Ink terminal UI (TypeScript, Ink 8, React 19)
    ├── package.json          npm run dev / npm run typecheck / npm test (node:test via tsx, *.test.ts)
    └── src/
        ├── index.tsx         render() in alternate screen; SettingsProvider + AnimationClock; q quits
        ├── paths.ts          REPO_ROOT
        ├── App.tsx           FLOW (GM thinking -> GM intro -> game) + SCREEN LAYOUT + key bindings. Add or move boxes here.
        ├── types.ts          TS mirror of the Python models + GameState + Action. Keep in sync with engine/models.
        ├── state.ts          read-only GameState helpers (playerPlacement, entityAt, tileAhead, directions)
        ├── bridge/
        │   └── useEngine.ts  spawns `uv run python -m engine.server`, JSON lines; returns {state, narration, narrating, message, loading, dispatch}
        ├── input/            KEYBOARD: always use these, never Ink's useInput directly
        │   ├── keys.ts       usePress (ignores key releases), useHoldKeys (movement: steady repeat while held)
        │   ├── holdRepeat.ts HoldRepeater: pure hold-to-repeat logic (kitty release events or OS-repeat fallback)
        │   └── holdRepeat.test.ts
        ├── settings/
        │   └── settings.tsx  Settings (typingSpeed, gmIntro, moveSpeed, smoothCamera), TYPING_SPEEDS, MOVE_SPEEDS, SettingsProvider/useSettings/useTypingCps, saved to .dnllm-settings.json
        ├── gm/
        │   ├── GameMasterScreen.tsx  full-screen GM card: "thinking" (LLM working, logo on first load) / "speaking" (typed chapter + room intro + goal)
        │   ├── EndingScreen.tsx  VICTORY/DEFEAT banner, typed epilogue, run stats; enter = new game
        │   └── art.ts        LOGO, VICTORY, DEFEAT + hooded GM frames (idle, blink, talking, thinking)
        ├── hud/
        │   └── StatusBar.tsx bottom line: HP, AC, weapon, statuses, room + keycap hints
        ├── story/
        │   ├── StoryText.tsx Game Master panel: latest narration, typed; "the game master writes..." while narrating
        │   ├── LogText.tsx   combat/event log under the 3D view (fresh lines bright)
        │   └── QuestPanel.tsx  current chapter, objective ☐/☑, chapter track ●─◆─○, exit sealed/open
        ├── combat/
        │   └── DamageText.tsx  DamageText (coloured "1d6 sharp + 1d4 fire"), Effectiveness (×2 weak), StatusList
        ├── components/       reusable building blocks
        │   ├── Panel.tsx     rounded box with title (and optional subtitle) set into the top border; every window is a Panel
        │   ├── SelectList.tsx  ↑/↓/enter list used by the menu tabs
        │   ├── StatBlock.tsx   stats row (or +/- buffs)
        │   ├── AnimatedArt.tsx plays an entity's current animation in a fixed-size box
        │   └── HpBar.tsx
        ├── render/
        │   ├── CellGrid.tsx  Cell type {char, color, dim} + component that draws a Cell[][]
        │   ├── animation.tsx AnimationClock (global tick, FPS=8), useTick(), framesOf/frameAt/frameBox
        │   └── useTypewriter.ts  typing animation hook: {shown, done, skip} at N chars/second
        ├── view3d/           first-person 3D view
        │   ├── raycast.ts    pure ASCII raycaster: tiles + camera + sprites + theme -> Cell[][]
        │   ├── themes.ts     theme name (from the LLM) -> wall/door/exit/floor/water colours
        │   ├── useSmoothCamera.ts  glides the camera between tiles/directions over one movement step
        │   └── FirstPersonView.tsx  turns GameState into camera + sprites, renders the grid
        ├── map/
        │   ├── glyphs.ts     how tiles/entities look on the minimap (TILE_GLYPHS, entityGlyph, player arrows)
        │   ├── Minimap.tsx   top-down window around the player
        │   └── NearbyList.tsx  legend: glyph -> entity name
        └── menu/             bottom 1/4 menu box
            ├── MenuBox.tsx   tab bar (←/→) + active tab
            ├── types.ts      MenuTab / TabProps
            └── tabs/         one file per tab; index.ts holds the TABS list
                ├── FightTab.tsx  pick an attack, see target HP/AC/statuses and how effective it is
                ├── ItemsTab.tsx (enter: ready weapon / drink potion), PartyTab.tsx, OptionsTab.tsx (Save / Load / Quit)
                ├── SettingsTab.tsx  enter cycles a setting (typing speed, move speed, smooth camera, GM intro)
                ├── StoryTab.tsx  chapters + journal of the highlighted chapter
                ├── DebugTab.tsx  dev commands; only visible when state.debug (./play --debug)
                └── index.ts
```

### Where to edit

| Task | File(s) |
|---|---|
| New enemy / NPC / item the LLM can spawn | add a `Spawnable` in `engine/data/catalog.py` + its sprite in `engine/data/sprites.py` (schema, prompt and validation update automatically) |
| New room layout or feature | builder in `engine/world/mapgen.py` (`LAYOUTS` / `FEATURES`) + a blurb in `catalog.py` |
| New room theme (look) | `THEMES` in `engine/data/catalog.py` + colours in `ui/src/view3d/themes.ts` |
| New damage type | subclass a category in `engine/combat/damage.py`, set id/name/color/description, implement `on_hit()`, `@register` (the UI picks it up from `damage_types`) |
| New damage category | subclass `DamageType` as an abstract class (like `MagicDamage`), then add types under it |
| New status effect | factory in `engine/combat/status.py`, applied from a damage type's `on_hit()` |
| New weapon / enemy attack / resistances | `_weapon(...)` / `_enemy(..., attacks, resist)` in `engine/data/catalog.py` |
| Player spells | `attacks=[...]` in `make_party()` in `engine/data/catalog.py` |
| Enemy behaviour | `engine/combat/ai.py` |
| The story (chapters, goals, NPC lines, ending texts) | `CAMPAIGN` in `engine/story/campaign.py` |
| New objective kind | `ObjectiveKind` in `campaign.py` + `StoryProgress.check()` in `engine/story/progress.py` |
| New boss | `BOSSES` in `engine/data/catalog.py` + sprite, then list it in a chapter's `enemies` |
| New dev/debug command | `engine/debug.py` + a row in `ui/src/menu/tabs/DebugTab.tsx` |
| What the LLM is told / asked | `SYSTEM_PROMPT`, `room_prompt()`, `room_schema()` in `engine/llm/room_director.py` |
| New player action | `Action` in `ui/src/types.ts` + `Game.handle()` in `engine/game.py` |
| Game rules | `engine/rules/` (movement is in `movement.py`) |
| New game object type or field | `engine/models/` + mirror it in `ui/src/types.ts` |
| New menu tab | new file in `ui/src/menu/tabs/` + add it to `TABS` in `tabs/index.ts` |
| New box/window on screen | `<Panel>` in `ui/src/App.tsx` |
| New key binding | `useInput` in `ui/src/App.tsx` (menu keys live in `MenuBox` / `SelectList`) |
| New tile type | `engine/models/world.py` + `SOLID`/`wallColor`/`floorCell` in `ui/src/view3d/raycast.ts` + `TILE_GLYPHS` in `ui/src/map/glyphs.ts` |
| How things look in 3D | sprite size/colour in `view3d/FirstPersonView.tsx`; the art itself is the entity's `art` field |
| Typing speed options / new setting | `TYPING_SPEEDS` / `Settings` + `DEFAULTS` in `ui/src/settings/settings.tsx`, row in `SettingsTab.tsx` |
| Game master look / intro screen | `ui/src/gm/art.ts`, `ui/src/gm/GameMasterScreen.tsx` |
| How combat is narrated | `SYSTEM_PROMPT` / `narrate()` in `engine/llm/narrator.py` |
| Movement feel (step rate, hold detection) | `MOVE_SPEEDS` in `settings.tsx`; `MIN_RELEASE_MS` etc. in `ui/src/input/holdRepeat.ts`; bindings in `useHoldKeys` call in `App.tsx` |
| Animation speed | `FPS` in `ui/src/render/animation.tsx` |
| LLM model or server flags | `scripts/llm-server.sh` |
| Launcher (checks, startup, cleanup, flags) | `main.py` (`./play` is a thin wrapper) |

### Shared data model

- Item kinds: `item`, `weapon` (`attack`), `potion` (`heal`). In the UI use `isItem(entity)`, not `kind === 'item'`.
- The map is `tiles: string[]`: `#` wall, `+` door (drawn as wall, can be walked through), `.` floor, `~` water, `>` exit (walking into it makes the next room). `map.theme` picks colours.
- Entities stand on the map through `placements: {id, x, y, facing?}`. Positions are whole tiles, and facing is `N|E|S|W`.
- Movement is on the grid: step forward or back, turn 90°. Walking onto an item picks it up. Walking into an enemy attacks it; walking into an NPC shows a dialogue line.
- Sprites: `art` is `{animationName: frames[]}`, where each frame is a multi-line ASCII string. Every entity has `idle`, and `animation` names the one playing now (Python: `entity.play("attack")`). The UI loops frames at 8 fps (16 frames = 2 s), and each entity starts at a different point in its loop based on its id. In 3D, spaces outside the drawing are see-through, and art is scaled by whole numbers (at most 3×) using the size of its biggest frame. Sprites are sized as if they were 0.5 tiles further away (`SPRITE_DISTANCE_BIAS`) and step down a size until they fit on screen. The field of view adapts to the view's shape (60–90°), so things up close never go off-screen.
- `party[0]` is the player. Party members travel with the player and aren't placed on the map. Characters also carry `total_stats` (base + item buffs) for the UI.
- GameState = `{room, run, party, entities, map, story, ending, stats, debug, log, log_fresh, damage_types}` from `Game.to_dict()`.

### Story

- One room = one chapter of `CAMPAIGN` (6 chapters, ending in a boss fight with the High Priest). Each chapter has an objective: `reach_exit`, `collect` (item), `talk` (NPC), `defeat_all`, `defeat_boss`.
- The LLM still designs the room, but `room_prompt()` adds the premise, the story so far, the chapter's guidance and goal, and the things guaranteed to be there. The schema only offers the chapter's themes. Python then adds the chapter's required enemies/NPCs/items (always placed first) and story NPC lines (said in order).
- The exit (`>`) stays sealed until the objective is done (`StoryProgress.exit_open()`). Walking out advances to the next chapter.
- The run ends with `game.ending`: victory when the last objective is done, defeat when the player dies. The server then asks the LLM for an epilogue (`write_epilogue`, fallback texts in the campaign) and the UI shows the ending screen. Enter sends `new_game`.
- The journal (`story.journal`) collects room narrations, NPC lines and completed goals; the STORY tab shows it per chapter.

### Dev tools

- `./play --debug`: DEBUG tab (teleport to any chapter, complete objective, kill all, heal, god mode, give weapons, reroll room, LLM rooms on/off, win/lose) and a debug badge in the status bar (position, god, `rnd` = random room).
- `./play --chapter end` (or `--chapter 3`) starts there; `--god` starts in god mode; both imply `--debug`. `--fast` skips GM intros and typing for that session. `--offline` skips the LLM entirely.
- Fastest way to check the ending: `./play --chapter end --god --fast --offline`, then DEBUG → Win now / Complete objective (or just kill the High Priest).
- Engine env equivalents: `DNLLM_DEBUG=1`, `DNLLM_START_CHAPTER=N|end`, `DNLLM_GOD=1`; UI: `DNLLM_FAST=1`.

### Screen flow and story

- Before every room: the GM "thinking" screen while the LLM builds it (the DnLLM logo on first load), then the GM "speaking" screen types the room narration. Enter skips the typing, and Enter again enters the room. It can be turned off in Settings.
- During play, the Game Master panel types the latest narration. After every action with combat, the server hands that turn's combat events to the narrator thread, which asks the LLM for a 1–2 sentence retelling (offline: the raw events). Only the newest one is shown, and a new room cancels any narration still pending.
- The typing speed (slow 25 / normal 50 / fast 110 cps / instant) applies to all typing animations and is set in the SETTINGS tab.

### Input and movement

- Terminals don't normally report key releases: holding a key gives one press, then nothing for the OS repeat delay (~0.5 s), then fast repeats. Acting on every event causes freeze-then-race and moves that keep going after release.
- `index.tsx` turns on the kitty keyboard protocol (`mode: 'auto'`) where the terminal supports it (kitty, Ghostty, WezTerm, iTerm2…), so keys come with press/repeat/release.
- Movement keys (w/s/a/d) go through `useHoldKeys` -> `HoldRepeater`, which steps at OUR rate (`MOVE_SPEEDS`, 180 ms by default; turning is 1.4×):
  - with release events: step on press, then every interval until release (linear from the first step);
  - without them (e.g. Apple Terminal): a tap is exactly one step; a hold is confirmed by the first OS repeat, then steps at our rate and stops when repeats stop (≤150 ms or 2.5× the repeat gap). The first OS repeat delay can't be avoided there.
- An action is only sent when the previous one has been answered (`busy()` in useEngine), so moves never queue up.
- `useSmoothCamera` glides the 3D camera over one step (`smoothCamera` setting), so holding a key moves continuously.
- Every other key handler uses `usePress`, which ignores release events (they'd otherwise act as a second press).
- Verified timing: kitty mode steps at 0/181/362/547 ms…; fallback at 0, ~500 (OS delay), then every ~180 ms; a tap = 1 move.

### Combat

- Turn-based. Moving, attacking, picking up and drinking cost a turn; turning, menus and swinging at nothing are free. After the player's turn: player statuses tick, then every hostile ticks its statuses and acts (attacks if adjacent, otherwise steps toward the player within 6 tiles).
- Attack: `f`, walking into an enemy (both use attack 0 = first weapon), or the FIGHT tab (any weapon or spell). Enter on a weapon in ITEMS readies it (moves it to the front).
- To hit: d20 + modifier(attack.stat) >= target `armor_class()` (10 + DEX mod - status penalties). A natural 1 misses. A roll >= the type's `crit_from` (20, Piercing 19) hits and doubles the dice.
- Damage: every `DamageRoll` is rolled, the stat modifier is added once, then each part is multiplied by `DamageType.multiplier(target)`. Resistances use the most specific key along `lineage()` (`dull` beats `physical`), and Piercing can't be resisted. Then `on_hit()` applies the type's effect (bleed, stun, burn, soak).
- Python sends `damage_types` (name, colour, lineage, description) and each character's `damage_multipliers`, so the UI never hardcodes combat rules.
- When the player dies, the server sends the final state, then calls `Game.reset()` and builds a new room 1.

### Engine <-> UI protocol (JSON lines over stdio)

- UI -> engine: `{"type": "action", "action": Action}` (incl. `{"type": "new_game"}` and, in debug, `{"type": "debug", "command", ...}`).
- When the run ends the engine sends the state with `ending.text == ""`, then `loading`, then the state with the epilogue.
- Engine -> UI: `{"type": "loading", "message"}` while the LLM builds a room, `{"type": "state", "state", "narration", "message"}` after every action, `{"type": "narrating"}` + later `{"type": "narration", "text"}` when combat happened (sent from the narrator thread), and `{"type": "error", "message"}`.
- The UI takes `narration` from a state message only when the room changes (`run:room` key); during play the newer `narration` messages win.
- The engine's stdout is only for protocol messages. Logs go to stderr, and the UI writes them to `engine.log`.

## Running

- **First time on a new machine:** `./setup` (asks before installing anything; `--yes` to skip the questions, `--no-model` to skip the 1.3 GB download). macOS and Linux; on Windows use WSL. Safe to re-run.
- **Play:** `./play` (or double-click `DnLLM.command`). It checks node 22+, npm, uv and llama-server, runs `npm install` in `ui/` on first run, reuses a llama-server already answering on the port or starts `scripts/llm-server.sh` itself (waiting for `/health`, with download progress on the very first run), then runs the UI. When the game exits (q or Ctrl+C) it stops the LLM server only if it started it.
  - `./play --offline`: no LLM (random rooms, raw combat log as narration). `--seed N`: repeatable dungeon. `--port P`: LLM port. `--check`: only check the tools. `--download`: download the model and exit (used by `./setup`).
  - Dev: `--debug`, `--chapter N|end`, `--god`, `--fast` (see "Dev tools" above).
- Manual: `./scripts/llm-server.sh` in one terminal, `cd ui && npm run dev` in another (the UI starts the Python engine itself).
- Engine alone (debug): `uv run python -m engine.server`, then type action JSON lines. `DNLLM_SEED=1` makes it deterministic, and `DNLLM_LLM_URL` points it at another server.
- Tests: `uv run pytest -q` (engine) and `cd ui && npm test` (UI logic). Typecheck UI: `cd ui && npm run typecheck`.
- Engine debug log (e.g. every player move): `DNLLM_LOG_LEVEL=DEBUG`, written to `engine.log`.

## LLM

- Model: Qwen3.5 2B (`unsloth/Qwen3.5-2B-GGUF:Q4_K_M`, ~1.3 GB), served by llama.cpp. The first run of the script downloads it from Hugging Face.
- OpenAI-compatible API at `http://127.0.0.1:8080/v1/chat/completions`. Thinking is turned off in the script.
- Room flow: `room_schema()` (enums built from the catalog) + `room_prompt()` -> LLM -> JSON `{theme, layout, features[], enemies[], npcs[], items[], name, narration}` -> `parse_room_plan()` (drops unknown ids, caps counts, trims cut-off narration) -> `build_room()` + `populate()`.
- If the server is down or the reply is unusable, `RoomDirector` uses `RandomLLM` instead (a random answer that fits the schema), and the UI shows "(LLM offline: random room)".
- A room takes about 3–4 s to generate (~50 tok/s on an M-series Mac).

## Git workflow

```
feature branch ──(fast-forward)──▶ rc ──(merge commit)──▶ main ──▶ push both to upstream
```

1. **Branch off `rc`** for each feature: `git checkout -b <feature> rc` (e.g. `llm-integration`, `combat`).
2. **Commit on the feature branch.** Before committing, run `uv run pytest -q`, `cd ui && npm test` and `npm run typecheck`, and update the project structure in this file.
3. **Merge the feature into `rc`:** `git checkout rc && git merge --ff-only <feature>`.
4. **Merge `rc` into `main`** with a merge commit and git's default message ("Merge branch 'rc'"): `git checkout main && git merge --no-edit rc`.
5. **Push both:** `git push upstream rc main`. The remote is called `upstream`, not `origin`.

Rules:
- **Never sign commits as Claude.** No `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" line, in commits or PRs.
- **Commit, merge or push only when asked.** Never commit directly to `rc` or `main`; they only receive merges.
- **Run `git fetch upstream` before merging,** to make sure `rc` and `main` aren't behind upstream.

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
