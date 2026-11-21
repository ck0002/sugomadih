import {Box, Text} from 'ink';
import type {GameState} from '../types.js';
import {entityGlyph} from './glyphs.js';

type Props = {state: GameState};

// Map legend: what each glyph on the map is.
export function NearbyList({state}: Props) {
	const playerId = state.party[0]?.id;
	return (
		<Box flexDirection="column">
			{state.map.placements.map(({id}) => {
				const entity = state.entities[id];
				if (!entity) return null;
				const g = entityGlyph(entity, id === playerId);
				return (
					<Text key={id} wrap="truncate">
						<Text color={g.color}>{g.char}</Text> {entity.name}
					</Text>
				);
			})}
		</Box>
	);
}
