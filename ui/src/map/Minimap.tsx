import {CellGrid, type Cell} from '../render/CellGrid.js';
import {playerPlacement} from '../state.js';
import type {GameState} from '../types.js';
import {entityGlyph, PLAYER_ARROWS, TILE_GLYPHS} from './glyphs.js';

type Props = {state: GameState; width: number; height: number};

// Top-down view of the map around the player. The arrow shows where you're facing.
export function Minimap({state, width, height}: Props) {
	const {map, entities} = state;
	const player = playerPlacement(state);
	const left = player.x - Math.floor(width / 2);
	const top = player.y - Math.floor(height / 2);

	const grid: Cell[][] = Array.from({length: height}, (_, row) =>
		Array.from({length: width}, (_, col) => {
			const ch = map.tiles[top + row]?.[left + col] ?? ' ';
			return TILE_GLYPHS[ch] ?? {char: ch};
		}),
	);

	for (const {id, x, y} of map.placements) {
		const entity = entities[id];
		const cell = grid[y - top]?.[x - left];
		if (!entity || !cell) continue;
		grid[y - top]![x - left] =
			id === player.id ? {char: PLAYER_ARROWS[player.facing ?? 'N'], color: 'whiteBright'} : entityGlyph(entity, false);
	}

	return <CellGrid grid={grid} />;
}
