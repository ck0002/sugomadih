// Read-only helpers for looking things up in GameState.
import type {Direction, Entity, GameState, Placement} from './types.js';

export const DIR_VECTORS: Record<Direction, [dx: number, dy: number]> = {
	N: [0, -1],
	E: [1, 0],
	S: [0, 1],
	W: [-1, 0],
};

export const TURN_RIGHT: Record<Direction, Direction> = {N: 'E', E: 'S', S: 'W', W: 'N'};
export const TURN_LEFT: Record<Direction, Direction> = {N: 'W', W: 'S', S: 'E', E: 'N'};

export function playerPlacement(state: GameState): Placement {
	const id = state.party[0]?.id;
	const p = state.map.placements.find(pl => pl.id === id);
	if (!p) throw new Error('player is not on the map');
	return p;
}

export function entityAt(state: GameState, x: number, y: number): Entity | undefined {
	const p = state.map.placements.find(pl => pl.x === x && pl.y === y);
	return p && state.entities[p.id];
}

// The tile right in front of the player.
export function tileAhead(state: GameState): {x: number; y: number} {
	const p = playerPlacement(state);
	const [dx, dy] = DIR_VECTORS[p.facing ?? 'N'];
	return {x: p.x + dx, y: p.y + dy};
}
