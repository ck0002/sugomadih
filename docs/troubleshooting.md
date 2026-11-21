# Troubleshooting

This page covers common issues when setting up or running the current repository.

## `uv` command not found

The frontend starts the Python engine by running `uv run --quiet python -m engine.server`. Make sure uv is installed and available on `PATH` in the same terminal environment used to start `npm run dev`.

After installing uv, open a new terminal if the shell has not refreshed its environment variables.

## Python version is too old

The project declares `requires-python = ">=3.14"`. Check the Python version available to uv and install/select Python 3.14 or newer before syncing the project environment.

## Frontend dependencies are missing

From the UI directory, run:

```bash
npm install
```

Then try:

```bash
npm run dev
```

## `llama-server` command not found

The project does not install llama.cpp. Install a compatible llama.cpp build separately and ensure that the `llama-server` executable is on `PATH` in the terminal where `scripts/llm-server.sh` is run.

The launcher uses the `-hf` flag and other llama-server options defined in the script. An older or incompatible build may not recognise them.

## The game starts but reports an offline LLM

The Python client defaults to `http://127.0.0.1:8080`. Check that:

1. `./scripts/llm-server.sh` is running in another terminal.
2. The server is listening on the expected port.
3. `DNLLM_LLM_URL` matches the server's base URL if you changed the port.
4. The local server has finished downloading/loading the model.

The game is designed to continue with `RandomLLM` when the server is unreachable. The offline notice therefore does not necessarily mean the game engine failed to start.

## Model download or startup fails

The first run may download the configured model. Confirm that the machine has network access and sufficient disk space, and inspect the llama-server terminal for its own error output. The model server is an external prerequisite and is not managed by `uv` or npm.

## Blank or malformed terminal output

Use a terminal with Unicode and ANSI colour support. Try increasing the terminal dimensions, because the UI uses multiple panels and a first-person render area. If the interface fails to start or the engine exits, inspect `engine.log` in the repository root.

## The engine exits or shows an error message

Inspect `engine.log`. The UI redirects the Python engine's stderr to this file. The engine protocol itself is written to stdout, so diagnostic output should be read from the log rather than from the JSON message stream.

You can also run the engine directly from the repository root:

```bash
uv run python -m engine.server
```

This is useful for debugging startup and protocol behaviour independently of the UI. In direct mode, enter newline-delimited JSON action messages to interact with the engine.

## Save or Load does not work

Save and Load are visible in the Options menu but are not implemented in the current engine. Selecting either option returns a not-implemented message. This is a known project limitation, not a local installation problem.

## Item selection appears to do nothing useful

The current `use_item` action is a placeholder. It displays a message but does not consume the selected item or activate an effect. Items can still be picked up and displayed in the inventory; their stat values contribute to the character's calculated total stats while carried.
