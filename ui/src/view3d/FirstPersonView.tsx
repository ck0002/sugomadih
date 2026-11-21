import {useMemo} from 'react';
import {CellGrid} from '../render/CellGrid.js';
import {DIR_VECTORS, playerPlacement} from '../state.js';
import type {GameState} from '../types.js';
import {entityGlyph} from '../map/glyphs.js';
import {renderScene, type Sprite} from './raycast.js';

type Props = {state: GameState; width: number; height: number};

// What the player sees: the map rendered in first person.
export function FirstPersonView({state, width, height}: Props) {
	const grid = useMemo(() => {
		const player = playerPlacement(state);
		const [dirX, dirY] = DIR_VECTORS[player.facing ?? 'N'];
		const camera = {x: player.x + 0.5, y: player.y + 0.5, dirX, dirY};
		return renderScene(state.map.tiles, camera, spritesFrom(state, player.id), width, height);
	}, [state, width, height]);

	return <CellGrid grid={grid} />;
}

function spritesFrom(state: GameState, playerId: string): Sprite[] {
	return state.map.placements.flatMap(({id, x, y}) => {
		const entity = state.entities[id];
		if (!entity || id === playerId) return [];
		const glyph = entityGlyph(entity, false);
		return [
			{
				x: x + 0.5,
				y: y + 0.5,
				art: entity.art,
				glyph: glyph.char,
				color: glyph.color ?? 'white',
				height: entity.kind === 'item' ? 0.3 : 0.75,
			},
		];
	});
}
