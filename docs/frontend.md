# Frontend and terminal renderer

The frontend is a TypeScript application built with React 19 and Ink 8. Ink provides the React component model for a terminal interface; the UI renders the state received from the Python engine.

## Startup

`ui/src/index.tsx` renders the root component in Ink's alternate screen. It also handles the global `Q` key and wraps the application in the shared `AnimationClock`.

The main `App` component:

- reads terminal dimensions;
- connects to the engine through `useEngine()`;
- binds `W`, `S`, `A`, and `D` to movement and turning actions;
- composes the main world view, Map, Story, Nearby, and bottom menu panels;
- shows a loading screen while no state is available.

## Engine bridge

`ui/src/bridge/useEngine.ts` starts the Python process with Node's `child_process.spawn()` and communicates over stdin/stdout using newline-delimited JSON.

The hook exposes:

- `state`: latest `GameState` or `null` before the first state arrives;
- `narration`: room narration;
- `message`: short feedback from the engine;
- `loading`: current loading text or `null`;
- `dispatch(action)`: writes an action message to the engine.

The child process's stderr is written to `engine.log`. The hook handles startup errors, engine exit, and cleanup when the UI unmounts.

## Main layout

`ui/src/App.tsx` creates the top world area and the bottom menu. The world area contains:

- `FirstPersonView` for the main first-person scene;
- `Minimap` for a top-down view around the player;
- `StoryText` for the current room narration and loading display;
- `NearbyList` for a legend of nearby entities.

Reusable UI building blocks live in `ui/src/components/`, including `Panel`, `SelectList`, `StatBlock`, `AnimatedArt`, and `HpBar`.

## First-person ASCII renderer

`ui/src/view3d/raycast.ts` is a pure TypeScript renderer. It receives map tiles, a camera, sprites, viewport dimensions, and theme colours, then returns a two-dimensional `Cell` grid.

The renderer uses a grid raycasting approach:

1. It calculates a camera plane and horizontal field of view based on viewport shape.
2. It draws floor cells below the horizon.
3. It casts one ray per output column to find the nearest wall-like tile.
4. It uses a depth buffer to prevent sprites from drawing through walls.
5. It projects entity sprites into the view and scales/clips their ASCII art.

The renderer treats `#`, `+`, and `>` as solid-looking surfaces for visual purposes. The Python movement rules still determine whether a tile can be entered.

Room colours are mapped in `ui/src/view3d/themes.ts`. The keys must match the room theme IDs in `engine/data/catalog.py`.

## Minimap and nearby list

The `map/` directory contains:

- `glyphs.ts` — tile and entity glyph mappings, including player direction arrows;
- `Minimap.tsx` — top-down map window around the player;
- `NearbyList.tsx` — nearby entity legend.

When adding a new tile or entity kind, verify whether its minimap glyph and display label need to be updated.

## Menus

`MenuBox.tsx` manages tab navigation with left and right arrow keys. The active tab is selected from `TABS` in `ui/src/menu/tabs/index.ts`.

Current tabs:

- `ItemsTab.tsx` — inventory list and item details;
- `PartyTab.tsx` — party members, HP, and stats;
- `OptionsTab.tsx` — New room, Save, Load, and Quit entries.

The UI may display an option before the engine implements it. Check [Gameplay](gameplay.md) and [Known limitations](known-limitations.md) for the current behaviour of each entry.

## Animation system

`ui/src/render/animation.tsx` provides a shared animation clock. The default animation rate is 8 frames per second. `framesOf()` selects the active animation's frames, `frameAt()` chooses a frame based on the clock and entity ID, and `frameBox()` calculates a stable maximum size for the art.

ASCII sprite data is stored in `engine/data/sprites.py` and serialized with each entity. Keep sprite frames reasonably sized for terminal display and ensure entities have an `idle` animation. Other animations are optional; `Entity.play()` falls back to `idle` when an animation name is missing.

## Keeping the frontend in sync

`ui/src/types.ts` mirrors the Python model serialization. When changing fields or adding a new entity property, update both ends. Also keep the engine message union in `useEngine.ts` in sync with the messages emitted by `engine/server.py`.

Run the static check with:

```bash
cd ui
npm run typecheck
```
