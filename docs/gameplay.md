# Gameplay and controls

DnLLM is currently an exploration-focused dungeon crawler. The player enters generated rooms, navigates the grid, encounters characters, collects items, and proceeds through exits. The interface is entirely terminal-based.

## Screen layout

The terminal screen is divided into two main areas:

- **World area:** a first-person ASCII view with the current room name, a minimap, room narration, and a nearby-entity list.
- **Menu area:** a tabbed panel at the bottom of the screen containing Items, Party, and Options.

The UI is designed for a terminal window large enough to display the side panels and the world view. Resizing the terminal changes the available render dimensions.

## Controls

| Key | Action |
|---|---|
| `W` | Move one tile forward |
| `S` | Move one tile backward |
| `A` | Rotate 90 degrees left |
| `D` | Rotate 90 degrees right |
| `←` | Select the previous menu tab |
| `→` | Select the next menu tab |
| `↑` | Move the menu selection up |
| `↓` | Move the menu selection down |
| `Enter` | Activate the selected menu entry |
| `Q` | Quit the application |

Movement keys are ignored while the engine is generating the next room.

## Exploring a room

Each room has a generated name, a theme, a layout, optional environmental features, and zero or more spawned entities. The map is a grid. The player moves one cell at a time and rotates to change facing direction.

Current tile meanings:

| Character | Meaning | Movement |
|---|---|---|
| `#` | Wall | Blocks movement |
| `.` | Floor | Walkable |
| `+` | Door | Walkable; rendered with a door appearance |
| `~` | Water | Walkable in the current movement rules |
| `>` | Exit | Entering it generates the next room |

The exit is placed on the outer edge of the generated map. The map generator and tests are designed to ensure that the walkable area is connected and that a generated room has one exit.

## Characters and encounters

The game currently represents party members, enemies, and NPCs using the `Character` model.

- **Party members** are displayed in the Party tab. The first party member (`party[0]`) is the player. The starting party also includes Brena, a dwarf cleric.
- **NPCs** are non-hostile characters. Bumping into one displays one of its dialogue lines as a short message.
- **Hostile characters** block the player's movement. When a hostile character is adjacent, the engine selects its `attack` animation if that animation exists.

The current implementation does **not** resolve an attack, calculate damage, or run a complete combat encounter. An attack animation is visual feedback only; it is not a combat system.

## Items and inventory

The player starts with a Rusty Sword and a Red Potion. Additional items may be placed in rooms by the room director and picked up by walking onto their tile.

The Items tab displays the inventory, item description, ASCII art, stat values, and gold value. A character's `total_stats` are calculated as base stats plus the stat bonuses of every item in that character's inventory.

Selecting an item currently sends a `use_item` action, but the engine only displays a placeholder message. It does not consume the item or trigger a use effect. As a result, inventory stat bonuses are currently passive while an item is carried; they are not activated by selecting it.

## Party tab

The Party tab lists the members of the current party. Selecting a member displays that character's art, description, HP bar, and total stats. The UI can request an inspection message for the selected member.

Party members travel with the player as party data; they are not all placed as independent map sprites.

## Options tab

The Options tab currently lists:

| Option | Current behaviour |
|---|---|
| `New room` | Generates the next room immediately |
| `Save` | Not implemented; the engine returns a not-implemented message |
| `Load` | Not implemented; the engine returns a not-implemented message |
| `Quit` | Exits the UI |

A room can also be left by walking into its `>` exit tile.

## Room generation and narration

When the next room is requested, the engine sends room context to the room director. If the local LLM is available, it chooses a theme, layout, features, enemies, NPCs, items, a room name, and a short narration from the allowed catalogues. If it is unavailable or returns an unusable response, the random fallback creates a valid plan instead.

The model's output determines room content choices and narration. It does not execute movement, validate collisions, or apply game rules. See [AI room director](ai-system.md).

## Current gameplay loop

The implemented loop is:

1. Generate a room and place the player at its start.
2. Read the narration and inspect the minimap / nearby list.
3. Move and turn to explore the room.
4. Pick up items by stepping onto them; characters block movement and may display dialogue or hostile animations.
5. Reach the exit or choose `New room` to generate another room.

Combat, item activation, saving, and loading are not part of the implemented loop yet. See [Known limitations](known-limitations.md).
