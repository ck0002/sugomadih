import {useMemo} from 'react';
import {frameAt, frameBox, framesOf, useTick} from '../render/animation.js';
import {CellGrid} from '../render/CellGrid.js';
import {DIR_VECTORS, playerPlacement} from '../state.js';
import {isItem, type GameState} from '../types.js';
import {entityGlyph} from '../map/glyphs.js';
import {renderScene, type Sprite} from './raycast.js';
import {themeFor} from './themes.js';
import {useSmoothCamera} from './useSmoothCamera.js';

type Props = {state: GameState; width: number; height: number; glideMs?: number};

// What the player sees: the map rendered in first person. The camera glides between tiles (useSmoothCamera).
export function FirstPersonView({state, width, height, glideMs = 0}: Props) {
	const tick = useTick();
	const player = playerPlacement(state);
	const [dirX, dirY] = DIR_VECTORS[player.facing ?? 'N'];
	const camera = useSmoothCamera({x: player.x + 0.5, y: player.y + 0.5, dirX, dirY}, glideMs);

	const grid = useMemo(
		() => renderScene(state.map.tiles, camera, spritesFrom(state, player.id, tick), width, height, themeFor(state.map.theme)),
		[state, camera, player.id, width, height, tick],
	);

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
				height: isItem(entity) ? 0.3 : 0.75,
			},
		];
	});
}
