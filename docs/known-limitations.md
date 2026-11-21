# Known limitations and future work

This page records the boundary between the current implementation and features that are not implemented yet. It is intended to prevent the README and gameplay guide from presenting planned functionality as if it already existed.

## Working in the current implementation

- Python owns the current game state and handles the supported player actions.
- The terminal UI starts the Python engine and exchanges JSON-line messages with it.
- Rooms are generated from configured layouts and environmental features.
- The room director can request a constrained room plan from the local LLM.
- Invalid or unavailable LLM output is handled by a random fallback.
- Enemies, NPCs, and items can be spawned from the catalogue.
- The player can move and turn, collide with walls and characters, pick up items, and enter an exit.
- NPC bumps can show dialogue text; hostile characters block movement and can play an adjacent attack animation.
- The UI displays a first-person ASCII scene, minimap, story text, nearby list, party data, and inventory details.
- Python engine tests cover key map, parser, fallback, movement-to-exit, pickup, and serialization behaviour.

## Not implemented or incomplete

| Area | Current state |
|---|---|
| Combat resolution | Not implemented. Hostiles block movement and may animate, but no attack rolls, damage, turn order, or defeat handling are applied. |
| Player/enemy damage loop | Not implemented as an encounter system. HP is represented in the models and shown in the UI, but the current movement/encounter path does not run combat. |
| Item usage | Not implemented. Selecting an item displays a placeholder message; it does not consume the item or activate a use effect. |
| Equipment/effect lifecycle | Item stats are added to a character's total stats while carried. There is no separate equip/unequip or consumable-effect system in the current action handler. |
| Save game | Not implemented. The Save menu entry returns a not-implemented message. |
| Load game | Not implemented. The Load menu entry returns a not-implemented message. |
| Inventory management | The UI displays inventory, but the current engine does not implement a full drop, equip, trade, or use workflow. |
| Merchant economy | The catalogue includes a merchant NPC and item gold values, but buying/selling is not implemented. |
| Character progression | No implemented level-up, experience, skill-check, or progression loop is exposed by the current game actions. |
| Key/lock puzzle | A brass key exists in the item catalogue, but door unlocking or key consumption is not implemented in the current movement rules. |
| Endgame / victory condition | No final objective or completed campaign flow is implemented in the current source. |

## Development priorities

A practical implementation order would be:

1. **Combat foundation:** define action economy, hit/damage rules, enemy turns, HP changes, defeat states, and tests.
2. **Item behaviour:** distinguish passive bonuses from consumables, define activation rules, and implement item consumption/effects.
3. **Persistence:** define a versioned save format and safely serialize/restore party, room, entities, and progression.
4. **NPC and merchant interactions:** move beyond bump dialogue to explicit interaction choices and trade rules.
5. **Progression and goals:** decide how abilities, rewards, room depth, difficulty, and campaign completion should work.
6. **Integration tests and balancing:** test longer sessions, model failures, and consistent gameplay outcomes.

These are recommendations based on the current source shape, not commitments or existing features.

## Keeping this page accurate

When a listed limitation is implemented, update this page and the relevant gameplay/README sections in the same change. Add tests for the behaviour before describing it as complete.
