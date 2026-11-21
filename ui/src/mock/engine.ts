// Stand-in for the Python engine so we can walk around before the bridge exists.
// Real rules (collision, bumping into enemies, ...) belong in Python; delete this once it's wired up.
import {DIR_VECTORS, entityAt, playerPlacement, TURN_LEFT, TURN_RIGHT} from '../state.js';
import type {Action, GameState} from '../types.js';

const BLOCKING = new Set(['#']);

export function applyMockAction(state: GameState, action: Action): {state: GameState; message?: string} {
	const result = applyAction(state, action);
	return {...result, state: updateAnimations(result.state)};
}

// Hostiles standing next to the player play "attack", everyone else "idle".
function updateAnimations(state: GameState): GameState {
	const player = playerPlacement(state);
	const entities = {...state.entities};
	for (const {id, x, y} of state.map.placements) {
		const e = entities[id];
		if (!e || id === player.id) continue;
		const adjacent = Math.abs(x - player.x) + Math.abs(y - player.y) === 1;
		const animation = e.kind === 'character' && e.hostile && adjacent && 'attack' in e.art ? 'attack' : 'idle';
		if (e.animation !== animation) entities[id] = {...e, animation};
	}
	return {...state, entities};
}

function applyAction(state: GameState, action: Action): {state: GameState; message?: string} {
	const player = playerPlacement(state);
	const facing = player.facing ?? 'N';

	const withPlayer = (changes: Partial<typeof player>): GameState => ({
		...state,
		map: {
			...state.map,
			placements: state.map.placements.map(p => (p.id === player.id ? {...p, ...changes} : p)),
		},
	});

	switch (action.type) {
		case 'turn':
			return {state: withPlayer({facing: (action.dir === 'left' ? TURN_LEFT : TURN_RIGHT)[facing]})};

		case 'move': {
			const [dx, dy] = DIR_VECTORS[facing];
			const sign = action.dir === 'forward' ? 1 : -1;
			const x = player.x + dx * sign;
			const y = player.y + dy * sign;
			const tile = state.map.tiles[y]?.[x];
			if (tile === undefined || BLOCKING.has(tile)) return {state, message: 'A wall blocks your way.'};
			const other = entityAt(state, x, y);
			if (other) return {state, message: `${other.name} is in the way.`};
			return {state: withPlayer({x, y})};
		}

		default:
			return {state, message: `→ ${JSON.stringify(action)}`};
	}
}
