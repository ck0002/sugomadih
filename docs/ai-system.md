# AI room director

The local language model acts as a **room director**. It chooses the content of the next room and writes a short narration. It does not control the player, execute game rules, calculate movement, or resolve combat.

## Components

- `engine/data/catalog.py` defines the content the model is allowed to select: enemies, NPCs, items, themes, layouts, and features.
- `engine/llm/client.py` defines the `LLMClient` protocol and its implementations.
- `engine/llm/room_director.py` builds the prompt and JSON schema, validates the response, and selects the fallback when necessary.
- `scripts/llm-server.sh` starts the configured local llama.cpp server.

## Room generation flow

1. `Game.next_room()` creates a `RoomContext` containing the room number, current party, and previous room name.
2. `RoomDirector.plan()` builds the schema and prompt.
3. `LlamaServerClient` sends an OpenAI-compatible chat-completions request with a JSON-schema response format.
4. The model returns a structured room plan.
5. `parse_room_plan()` validates every selected ID and applies defaults and count limits.
6. `engine/world/mapgen.py` builds the tile layout.
7. `engine/world/spawn.py` turns the selected IDs into entities and places them on available map cells.
8. `Game` stores the room narration and state; the UI displays them.

## Allowed response fields

The generated JSON object contains:

| Field | Meaning |
|---|---|
| `theme` | Room visual theme selected from `THEMES` |
| `layout` | Map layout selected from `LAYOUTS` |
| `features` | Environmental features, maximum 2 |
| `enemies` | Enemy IDs, maximum 4 |
| `npcs` | NPC IDs, maximum 1 |
| `items` | Item IDs, maximum 3 |
| `name` | Room name, maximum 40 characters |
| `narration` | Short room description, maximum 300 characters |

The system prompt asks for no more than two short narration sentences and fewer than 40 words. The parser also limits the returned text length and trims a cut-off narration back to a completed sentence where possible.

## Content catalogues

The current catalogues define:

- **Themes:** `cellar`, `crypt`, `cave`, `sewer`.
- **Layouts:** `hall`, `pillared`, `cross`, `cave`, `chambers`.
- **Features:** `water`, `rubble`, `pillars`.
- **Enemies:** `goblin`, `giant_rat`, `skeleton`, `slime`, `cultist`.
- **NPCs:** `merchant`, `hermit`.
- **Items:** `rusty_sword`, `red_potion`, `owl_amulet`, `brass_key`, `gold_coins`, `torch`.

The schema enumerations are generated from these dictionaries. Adding an item or enemy to the catalogue therefore makes its ID available to the schema and prompt, provided its factory and supporting sprite data are valid.

## Difficulty guidance

The room prompt changes its difficulty guidance based on the room number:

- First room: gentle, with zero or one weak enemy.
- Rooms 2–3: one or two weak or medium enemies.
- Room 4 onward: up to four enemies, with stronger choices allowed.

This is prompt guidance for content selection, not a combat-balance system. The current engine does not implement combat resolution.

## Validation and limits

The model is not trusted to create arbitrary game objects. `parse_room_plan()`:

- accepts only IDs that exist in the current catalogues;
- applies defaults for missing or invalid theme/layout/name/narration fields;
- discards invalid IDs in arrays;
- caps array lengths;
- removes duplicate feature and NPC IDs;
- normalizes whitespace and limits text lengths;
- supplies a fallback plan if the input is not a dictionary or fields are malformed.

The JSON schema constrains the model at generation time, but the parser validates the result again before it reaches the engine.

## LLM client and fallback

`LlamaServerClient` calls:

```text
{DNLLM_LLM_URL}/v1/chat/completions
```

The default base URL is `http://127.0.0.1:8080`. The request includes a system prompt, room prompt, JSON schema, token limit, and temperature. Network failures, timeouts, malformed responses, and unusable JSON are represented as `LLMError`.

`RoomDirector` catches `LLMError` and asks the configured fallback client for a compatible response. The current fallback is `RandomLLM`, which recursively samples values that fit the supplied JSON schema. It does not require a model server.

The engine marks fallback-generated room plans with `source="fallback"`, and the UI shows `(LLM offline: random room)` in the action message.

## Configured local model

The launcher configures:

- Hugging Face model reference: `unsloth/Qwen3.5-2B-GGUF:Q4_K_M`.
- Context size: `8192`.
- Default server port: `8080` (overridable with `LLM_PORT`).
- Chat-template setting: `enable_thinking=false`.

The repository launcher expects `llama-server` to be installed separately. It does not install llama.cpp.

## Extending AI-generated content

To add content:

1. Add a `Spawnable` entry in the relevant dictionary in `engine/data/catalog.py`.
2. Provide the entity factory and the correct model type (`Character` or `Item`).
3. Add or select suitable ASCII art from `engine/data/sprites.py`.
4. Add or update tests for the new catalogue entry and its expected behaviour.
5. Update this document if the public content list or room-plan fields change.

For a new visual theme, update both `THEMES` in `engine/data/catalog.py` and the colour mapping in `ui/src/view3d/themes.ts`.
