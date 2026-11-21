# Installation and setup

This guide explains how to install the dependencies and launch the current DnLLM implementation.

## 1. Prerequisites

Install the following tools before starting:

1. **Python 3.14 or newer.** The required version is declared in `pyproject.toml` and `uv.lock`.
2. **uv.** The project uses uv to resolve the Python environment and run the engine and tests.
3. **Node.js and npm.** The terminal interface is a TypeScript application run through `tsx`.
4. **A Unicode-capable terminal.** The interface uses box drawing, sprite characters, and terminal colours.
5. **Optional: llama.cpp with `llama-server`.** This is required only for model-generated room plans. The executable must be available on `PATH`.

The repository's LLM launcher is `scripts/llm-server.sh`, a Bash script. On Windows, use WSL or another Bash environment, or start `llama-server` independently. The code does not currently include a dedicated native Windows launcher.

## 2. Get the source

```bash
git clone https://github.com/ck0002/sugomadih.git
cd sugomadih
```

All root-level Python commands below should be run from this directory unless stated otherwise.

## 3. Install Python dependencies

```bash
uv sync --dev
```

This creates or updates the uv-managed environment using the project metadata and lockfile. The Python engine currently relies on the standard library; `pytest` is the declared development dependency.

The frontend starts the engine with the command `uv run --quiet python -m engine.server`, so `uv` must be callable from the environment in which the UI is launched.

## 4. Install frontend dependencies

```bash
cd ui
npm install
```

The relevant npm scripts are:

- `npm run dev` — launches the terminal UI.
- `npm run typecheck` — runs the TypeScript compiler without emitting files.

Return to the repository root when using Python or launcher commands:

```bash
cd ..
```

## 5. Optional: prepare the local LLM server

The launcher at `scripts/llm-server.sh` runs `llama-server` with:

- Hugging Face model: `unsloth/Qwen3.5-2B-GGUF:Q4_K_M`
- context size: `8192`
- default port: `8080`
- thinking disabled in the chat-template settings

Start it from the repository root:

```bash
./scripts/llm-server.sh
```

The first run may need to download the model. Keep this terminal open while playing with the LLM enabled. The Python client expects an OpenAI-compatible chat completions endpoint at `http://127.0.0.1:8080/v1/chat/completions` by default.

The project does not install llama.cpp itself. Install a compatible build separately and make sure the `llama-server` executable supports the flags used in the repository launcher, including `-hf`.

## 6. Launch the game

Open a second terminal at the repository root and run:

```bash
cd ui
npm run dev
```

The React Ink UI starts the Python engine as a child process. You do not need to start `engine/server.py` separately for normal gameplay.

## 7. Run without an LLM

A local model server is optional. Start the UI in the same way:

```bash
cd ui
npm run dev
```

The engine first tries the configured LLM endpoint. If the request fails, `RoomDirector` invokes its `RandomLLM` fallback and generates a schema-compatible random room plan. Fallback rooms are marked in the UI with `(LLM offline: random room)`.

This mode is suitable for testing the existing exploration and movement loop without downloading the model.

## 8. Configuration

### Change the model server port

Start the model server on another port:

```bash
LLM_PORT=8081 ./scripts/llm-server.sh
```

Then launch the UI with the matching base URL:

```bash
cd ui
DNLLM_LLM_URL=http://127.0.0.1:8081 npm run dev
```

`DNLLM_LLM_URL` is a base URL. The Python client adds `/v1/chat/completions` itself; do not include that path in the environment variable.

### Set a deterministic engine seed

For a reproducible engine/random-fallback run, set `DNLLM_SEED` before launching. For example:

```bash
cd ui
DNLLM_SEED=123 npm run dev
```

The seed controls the engine's random generator and the random fallback. It does not make a generative LLM response deterministic.

### Run the engine directly for debugging

From the repository root:

```bash
uv run python -m engine.server
```

This starts the JSON-lines server in the terminal. It writes protocol messages to stdout and logs to stderr. See [Architecture](architecture.md) for the message format. This direct mode is primarily for development; normal gameplay starts the process through the UI.

## 9. Verify the installation

Run the Python tests:

```bash
uv run pytest -q
```

Run the frontend type check:

```bash
cd ui
npm run typecheck
```

See [Testing](testing.md) for the scope of the existing tests.

## 10. Runtime files

The UI redirects the Python engine's stderr output to `engine.log` in the repository root. This keeps log messages from interfering with the terminal interface. The log is useful when diagnosing engine startup, LLM, or action-handling errors.
