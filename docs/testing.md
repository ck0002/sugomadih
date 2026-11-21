# Tests and validation

The repository uses pytest for Python engine tests and TypeScript's compiler for frontend type checking.

## Run the Python tests

From the repository root:

```bash
uv run pytest -q
```

The tests use `RandomLLM` and seeded random generators where appropriate. A running llama.cpp server and downloaded model are not required for the existing suite.

## Run the frontend type check

From the UI directory:

```bash
npm run typecheck
```

This invokes `tsc --noEmit` using the settings in `ui/tsconfig.json`. It checks the TypeScript source without producing JavaScript output.

## Current test coverage

`tests/test_engine.py` currently checks the following areas:

### Procedural map invariants

- Every configured layout can be generated with the tested features.
- Each generated test map contains exactly one exit.
- The exit is on the outer map boundary.
- Every non-wall tile is reachable from the start.

### Room-plan parsing

- Unknown layout and entity IDs are rejected or dropped in favour of valid defaults.
- Non-dictionary or malformed model output does not crash the parser.
- Cut-off narration is trimmed to a completed sentence where possible.
- JSON schema enumerations are derived from the current catalogue IDs.

### LLM fallback

- An unreachable llama-server endpoint causes the room director to use the random fallback.
- The fallback plan uses a valid configured layout.

### Game loop and serialization

- Walking a path to the room exit requests a new room.
- Walking onto an item transfers it to the player's inventory and removes it from the room entity collection.
- The game state can be serialized to JSON and includes the data expected by the UI, including `total_stats`.

## What the tests do not establish

Passing the current tests does not mean every game feature is complete. The suite does not currently validate a full combat system, item-use effects, save/load persistence, long-session balancing, terminal rendering quality across all terminals, or the quality of generated narration. Those areas need additional tests as the features are implemented.

## Adding tests

When changing the engine:

1. Add tests close to the existing scenario or invariant in `tests/test_engine.py`, or create a focused test module if the suite grows.
2. Prefer deterministic seeds and `RandomLLM` for tests that do not need to evaluate model quality.
3. Test both expected results and failure/malformed-input paths.
4. For map generation, test invariants across several layouts and seeds rather than a single example.
5. Keep tests independent of an external network service unless a test is explicitly an integration test.
