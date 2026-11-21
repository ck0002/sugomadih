import {Box, Text} from 'ink';
import {frameAt, frameBox, framesOf, useTick} from '../render/animation.js';
import type {Animations} from '../types.js';

type Props = {entity: {id: string; art: Animations; animation: string}; color?: string};

// Plays an entity's current animation in a fixed-size box (sized to its biggest frame).
export function AnimatedArt({entity, color}: Props) {
	const tick = useTick();
	const {width, height} = frameBox(framesOf(entity));
	return (
		<Box width={width} height={height} flexShrink={0}>
			<Text color={color}>{frameAt(entity, tick)}</Text>
		</Box>
	);
}
