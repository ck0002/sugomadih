import type {Cell} from '../render/CellGrid.js';
import type {Direction, Entity} from '../types.js';

// How map tiles look on the minimap. Add new tile types here.
export const TILE_GLYPHS: Record<string, Cell> = {
	'#': {char: '#', color: 'gray'},
	'.': {char: '·', dim: true},
	'+': {char: '+', color: 'yellow'},
	'~': {char: '~', color: 'blue'},
	' ': {char: ' '},
};

export const PLAYER_ARROWS: Record<Direction, string> = {N: '▲', E: '►', S: '▼', W: '◄'};

// How entities look on the minimap and in the legend.
export function entityGlyph(entity: Entity, isPlayer: boolean): Cell {
	if (isPlayer) return {char: '@', color: 'whiteBright'};
	if (entity.kind === 'item') return {char: '!', color: 'cyan'};
	const char = entity.name[0]!.toLowerCase();
	return entity.hostile ? {char, color: 'red'} : {char: char.toUpperCase(), color: 'green'};
}
