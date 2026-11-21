import {useMemo} from 'react';
import {frameAt, frameBox, framesOf, useTick} from '../render/animation.js';
import {CellGrid} from '../render/CellGrid.js';
import {DIR_VECTORS, playerPlacement} from '../state.js';
import type {GameState} from '../types.js';
import {entityGlyph} from '../map/glyphs.js';
import {renderScene, type Sprite} from './raycast.js';
import {themeFor} from './themes.js';

type Props = {state: GameState; width: number; height: number};

// What the player sees: the map rendered in first person.
export function FirstPersonView({state, width, height}: Props) {
	const tick = useTick();
	const grid = useMemo(() => {
		const player = playerPlacement(state);
		const [dirX, dirY] = DIR_VECTORS[player.facing ?? 'N'];
		const camera = {x: player.x + 0.5, y: player.y + 0.5, dirX, dirY};
		return renderScene(state.map.tiles, camera, spritesFrom(state, player.id, tick), width, height, themeFor(state.map.theme));
	}, [state, width, height, tick]);

	return <CellGrid grid={grid} />;
}

function spritesFrom(state: GameState, playerId: string, tick: number): Sprite[] {
	return state.map.placements.flatMap(({id, x, y}) => {
		const entity = state.entities[id];
		if (!entity || id === playerId) return [];
		const glyph = entityGlyph(entity, false);
		const box = frameBox(framesOf(entity));
		return [
			{
				x: x + 0.5,
				y: y + 0.5,
				art: frameAt(entity, tick),
				artWidth: box.width,
				artHeight: box.height,
				glyph: glyph.char,
				color: glyph.color ?? 'white',
				height: entity.kind === 'item' ? 0.3 : 0.75,
			},
		];
	});
}
