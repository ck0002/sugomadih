import type {ReactNode} from 'react';
import {Box, Text, type BoxProps} from 'ink';

type Props = BoxProps & {
	title?: string;
	color?: string;
	children?: ReactNode;
};

// A bordered box with an optional title. Every window on screen is one of these,
// so a new box is just <Panel title="...">...</Panel> dropped into a layout.
export function Panel({title, color = 'white', children, ...box}: Props) {
	return (
		<Box borderStyle="round" borderColor={color} flexDirection="column" paddingX={1} overflow="hidden" {...box}>
			{title && (
				<Text bold color={color}>
					{title}
				</Text>
			)}
			{children}
		</Box>
	);
}
