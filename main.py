"""DnLLM launcher: checks tools, installs UI deps, starts the local LLM if needed, runs the game, cleans up.

    ./play                 normal start (reuses an LLM server that's already running)
    ./play --offline       no LLM: rooms are random, combat narration is the raw log
    ./play --seed 6        deterministic dungeon
    ./play --port 8091     run/use the LLM on another port
    ./play --check         only check that everything is installed

Dev options:
    ./play --debug                 DEBUG tab (teleport, god mode, kill all, win/lose...) + debug HUD
    ./play --chapter end           start at the last chapter (or --chapter 3); implies --debug
    ./play --god                   start in god mode; implies --debug
    ./play --fast                  no game master intros, instant text (this session only)
    ./play --chapter end --god --fast --offline   straight to the boss, instantly

Same as `uv run main.py ...`. Standard library only, so it runs before anything is installed.
"""

import argparse
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI = ROOT / "ui"
LLM_SCRIPT = ROOT / "scripts" / "llm-server.sh"
LLM_LOG = ROOT / "llm-server.log"
LLM_START_TIMEOUT = 15 * 60  # first run downloads ~1.3 GB
MIN_NODE = 22

LOGO = r"""
 ____        _     _     __  __
|  _ \ _ __ | |   | |   |  \/  |
| | | | '_ \| |   | |   | |\/| |
| |_| | | | | |___| |___| |  | |
|____/|_| |_|_____|_____|_|  |_|
"""

# ---- output ------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def step(text: str) -> None:
    print(color("◆ ", "35") + text)


def ok(text: str) -> None:
    print(color("  ✓ ", "32") + text)


def warn(text: str) -> None:
    print(color("  ! ", "33") + text)


def fail(text: str, hint: str = "") -> "SystemExit":
    print(color("  ✗ ", "31") + text)
    if hint:
        print(color("    → ", "2") + hint)
    return SystemExit(1)


def status_line(text: str) -> None:
    """Rewrite the current line (progress)."""
    if USE_COLOR:
        sys.stdout.write("\r\033[K" + color("  … ", "36") + text)
        sys.stdout.flush()


def end_status_line() -> None:
    if USE_COLOR:
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()


# ---- checks ------------------------------------------------------------------


def check_tools(need_llm: bool) -> None:
    step("Checking tools")
    node = shutil.which("node")
    if not node:
        raise fail("node not found", "install Node.js 22+: brew install node")
    version = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    major = int(re.match(r"v(\d+)", version).group(1)) if re.match(r"v(\d+)", version) else 0
    if major < MIN_NODE:
        raise fail(f"node {version} is too old (need {MIN_NODE}+)", "brew upgrade node")
    ok(f"node {version}")

    if not shutil.which("npm"):
        raise fail("npm not found", "it comes with Node.js: brew install node")
    ok("npm")

    if shutil.which("uv"):
        ok("uv")
    else:
        warn("uv not on PATH (fine if you started this some other way)")

    if need_llm:
        if not shutil.which("llama-server"):
            raise fail("llama-server not found", "brew install llama.cpp   (or play without the LLM: ./play --offline)")
        ok("llama-server")


def ensure_ui_deps() -> None:
    if (UI / "node_modules").is_dir():
        return
    step("Installing UI dependencies (first run)")
    result = subprocess.run(["npm", "install", "--no-fund", "--no-audit"], cwd=UI)
    if result.returncode != 0:
        raise fail("npm install failed", f"try it yourself: cd {UI} && npm install")
    ok("installed")


# ---- LLM server --------------------------------------------------------------


def llm_healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url + "/health", timeout=1) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def port_in_use(port: int) -> bool:
    import socket

    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def last_log_line() -> str:
    try:
        lines = LLM_LOG.read_text(errors="replace").replace("\r", "\n").strip().splitlines()
        return lines[-1][-90:] if lines else ""
    except OSError:
        return ""


def start_llm(url: str, port: int) -> subprocess.Popen | None:
    """Start llama-server if nothing is serving yet. Returns the process if we started it (we stop it later)."""
    step("Game master (local LLM)")
    if llm_healthy(url):
        ok(f"already running at {url}, using it")
        return None
    if port_in_use(port):
        raise fail(f"port {port} is busy but not answering like llama-server", "pick another: ./play --port 8091")

    log = open(LLM_LOG, "w")
    proc = subprocess.Popen(
        [str(LLM_SCRIPT)],
        cwd=ROOT,
        env={**os.environ, "LLM_PORT": str(port)},
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,  # Ctrl+C in the game must not kill it; we stop it ourselves
    )
    started = time.monotonic()
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while not llm_healthy(url):
        if proc.poll() is not None:
            end_status_line()
            tail = "\n".join(LLM_LOG.read_text(errors="replace").splitlines()[-8:])
            print(color(tail, "2"))
            raise fail(f"llama-server exited (code {proc.returncode}), full log: {LLM_LOG}", "or play without it: ./play --offline")
        elapsed = time.monotonic() - started
        if elapsed > LLM_START_TIMEOUT:
            stop_llm(proc)
            raise fail("the model took too long to load", f"see {LLM_LOG}")
        detail = last_log_line()
        downloading = "download" in detail.lower() or "%" in detail
        label = "downloading the model (first run only, ~1.3 GB)" if downloading else "loading the model"
        status_line(f"{frames[i % len(frames)]} {label}  {int(elapsed)}s  {color(detail, '2') if downloading else ''}")
        i += 1
        time.sleep(0.25)
    end_status_line()
    ok(f"ready at {url} ({int(time.monotonic() - started)}s)")
    return proc


def stop_llm(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


# ---- game --------------------------------------------------------------------


def run_game(env: dict[str, str]) -> int:
    step("Starting the game  " + color("(q to quit)", "2"))
    time.sleep(0.4)
    # The game owns the terminal; Ctrl+C goes to it, the launcher waits and cleans up afterwards.
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        return subprocess.run(["npm", "run", "--silent", "dev"], cwd=UI, env=env).returncode
    finally:
        signal.signal(signal.SIGINT, previous)


def main() -> None:
    parser = argparse.ArgumentParser(prog="play", description="Launch DnLLM.")
    parser.add_argument("--offline", action="store_true", help="don't use the LLM (random rooms, raw combat log)")
    parser.add_argument("--seed", type=int, help="seed for a repeatable dungeon")
    parser.add_argument("--port", type=int, default=8080, help="LLM server port (default 8080)")
    parser.add_argument("--check", action="store_true", help="only check that the tools are installed")
    dev = parser.add_argument_group("dev options")
    dev.add_argument("--debug", action="store_true", help="DEBUG tab (teleport, god mode, kill all, win/lose) + debug HUD")
    dev.add_argument("--chapter", metavar="N|end", help="start at story chapter N, or 'end' for the final chapter (implies --debug)")
    dev.add_argument("--god", action="store_true", help="start in god mode (implies --debug)")
    dev.add_argument("--fast", action="store_true", help="skip game master intros and typing animations (this session only)")
    args = parser.parse_args()
    if args.chapter is not None or args.god:
        args.debug = True
    if args.chapter is not None and not (args.chapter.isdigit() or args.chapter.lower() in ("end", "last", "boss", "final")):
        parser.error("--chapter takes a number (1, 2, ...) or 'end'")

    print(color(LOGO, "95"))
    check_tools(need_llm=not args.offline)
    if args.check:
        ensure_ui_deps()
        ok("all good. Run ./play to start.")
        return
    ensure_ui_deps()

    url = f"http://127.0.0.1:{args.port}"
    env = dict(os.environ)
    llm = None
    if args.offline:
        step("Offline mode: rooms are random, the game master stays quiet")
        env["DNLLM_LLM_URL"] = "http://127.0.0.1:9"  # nothing listens there -> engine falls back instantly
    else:
        env["DNLLM_LLM_URL"] = url
    if args.seed is not None:
        env["DNLLM_SEED"] = str(args.seed)
    if args.debug:
        env["DNLLM_DEBUG"] = "1"
        details = [f"chapter {args.chapter}" if args.chapter else "", "god mode" if args.god else ""]
        step("Debug mode " + color(" ".join(d for d in details if d) or "(DEBUG tab in the menu)", "2"))
    if args.chapter is not None:
        env["DNLLM_START_CHAPTER"] = args.chapter
    if args.god:
        env["DNLLM_GOD"] = "1"
    if args.fast:
        env["DNLLM_FAST"] = "1"

    code = 0
    try:
        if not args.offline:
            llm = start_llm(url, args.port)
        code = run_game(env)
    except KeyboardInterrupt:
        end_status_line()
        print()
        warn("cancelled")
        code = 130
    finally:
        if llm is not None:
            step("Stopping the game master")
            stop_llm(llm)
            ok("stopped")
    if code not in (0, 130):
        warn(f"the game exited with code {code}; engine log: {ROOT / 'engine.log'}")
    sys.exit(code)


if __name__ == "__main__":
    main()
