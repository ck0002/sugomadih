# Documentation

This directory contains the user guide and technical documentation for DnLLM.

## User guide

- [Installation and setup](installation.md) — prerequisites, dependency installation, local LLM setup, launch modes, and configuration.
- [Gameplay and controls](gameplay.md) — movement, menus, rooms, characters, items, and current player actions.
- [Troubleshooting](troubleshooting.md) — common setup and runtime problems.

## Technical documentation

- [Architecture](architecture.md) — system boundaries, process model, and engine/UI protocol.
- [AI room director](ai-system.md) — prompt construction, structured output, validation, and fallback behaviour.
- [Game engine](game-engine.md) — game models, room lifecycle, procedural maps, spawning, and current rules.
- [Frontend](frontend.md) — React Ink layout, input handling, raycaster, minimap, and animation.
- [Development](development.md) — extension points, coding conventions, and local workflow.
- [Testing](testing.md) — test commands and what the existing suite verifies.
- [Known limitations](known-limitations.md) — implemented features versus unfinished or absent features.

The root [README](../README.md) is the entry point for new users. Documentation is based on the repository source reviewed for this package; update these pages whenever implementation details change.
