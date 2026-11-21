# Development guide

This page describes where to make common changes and which contracts must remain consistent.

## Development setup

From the repository root:

```bash
uv sync --dev
cd ui
npm install
```

For normal UI development:

```bash
cd ui
npm run dev
```

The UI starts the Python engine automatically. You can leave the LLM server stopped while working on engine/UI features that do not require model quality; the random fallback keeps room generation available.

## Common extension points

| Change | Main files |
|---|---|
| Add an enemy, NPC, or item that the model can select | `engine/data/catalog.py`; add or reuse art in `engine/data/sprites.py` |
| Add a room layout | `engine/world/mapgen.py`; add its description to `LAYOUTS` in `engine/data/catalog.py` |
| Add an environmental feature | `engine/world/mapgen.py`; add its description to `FEATURES` in `engine/data/catalog.py` |
| Add a room theme | `engine/data/catalog.py` and `ui/src/view3d/themes.ts` |
| Change the LLM prompt or output schema | `engine/llm/room_director.py` |
| Change model server flags or model ID | `scripts/llm-server.sh` |
| Add a player action | `ui/src/types.ts`, `engine/game.py`, and the relevant UI input/menu component |
| Change movement rules | `engine/rules/movement.py` |
| Add a model field | `engine/models/` and `ui/src/types.ts` |
| Add a menu tab | create a component in `ui/src/menu/tabs/` and register it in `tabs/index.ts` |
| Change the screen layout | `ui/src/App.tsx` |
| Change map glyphs | `ui/src/map/glyphs.ts` |
| Change first-person rendering | `ui/src/view3d/raycast.ts` or `FirstPersonView.tsx` |
| Change animation rate | `FPS` in `ui/src/render/animation.tsx` |

## Important contracts

### Python and TypeScript data models

Python owns the serializable game models. `ui/src/types.ts` is a TypeScript mirror used by the UI. If a Python field changes, update the mirror and any components that consume it in the same change.

### Engine/UI protocol

The protocol is JSON lines over stdin/stdout. Every message must fit on one line and be valid JSON. Keep stdout free of logs and diagnostic output; use stderr for logging. Update both `engine/server.py` and `ui/src/bridge/useEngine.ts` if a message shape changes.

### LLM content catalogue

The room director builds JSON schema enums from dictionaries in `engine/data/catalog.py`. Do not let the model invent arbitrary IDs. Add a corresponding factory and valid sprite data for each new spawnable entry.

### Theme keys

A room theme ID must exist in both the Python theme catalogue and the frontend theme-colour mapping. The renderer uses a fallback theme if it receives an unknown key, but new themes should be wired correctly on both sides.

### Map tile definitions

When adding a tile character, review all of the following:

- constants and blocking behaviour in `engine/models/world.py`;
- map generation and movement behaviour in `engine/world/mapgen.py` and `engine/rules/movement.py`;
- wall/floor rendering in `ui/src/view3d/raycast.ts`;
- minimap glyphs in `ui/src/map/glyphs.ts`.

### Entity art

Sprite art is stored as strings in `engine/data/sprites.py`. Every entity should have an `idle` animation. Other animation names are optional. Keep art readable in a monospace terminal and avoid excessively wide frames.

## Suggested change workflow

1. Identify the engine model/rule that owns the behaviour.
2. Implement the change in Python first when it affects game state or rules.
3. Update the TypeScript type mirror and UI presentation as needed.
4. Add a focused test for the new behaviour or changed invariant.
5. Run `uv run pytest -q`.
6. Run `cd ui && npm run typecheck`.
7. Update the relevant user and technical documentation.
8. Review the complete diff for protocol, catalogue, tile, or model mismatches.

## Style and maintainability

- Keep game rules in the Python engine, not in React components.
- Prefer small, focused rule functions and reusable UI components.
- Keep model output constrained and validate it before use.
- Keep random behaviour controllable through the engine's seeded random generator where practical.
- Treat the JSON-lines protocol and the Python/TypeScript type mirror as explicit interfaces.
- Update documentation in the same change as user-visible behaviour.
