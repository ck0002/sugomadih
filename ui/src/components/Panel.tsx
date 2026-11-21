import type {ReactNode} from 'react';
import {Box, Text, type BoxProps} from 'ink';

type Props = BoxProps & {
	title?: string;
	subtitle?: string; // shown on the right side of the top border
	color?: string; // border + title colour
	titleColor?: string;
	subtitleColor?: string;
	children?: ReactNode;
};

const FILL = '─'.repeat(400); // clipped to whatever width the border has

// A rounded box with its title set into the top border:  ╭─┤ Story ├────────┤ 3 hp ├─╮
// Every window on screen is one of these, so a new box is just <Panel title="...">...</Panel>.
export function Panel({title, subtitle, color = 'gray', titleColor, subtitleColor, children, ...box}: Props) {
	return (
		<Box flexDirection="column" {...box}>
			<Box height={1} flexShrink={0}>
				<Text color={color}>{title ? '╭─┤' : '╭─'}</Text>
				{title && (
					<Box flexShrink={0}>
						<Text bold color={titleColor ?? color}>{` ${title} `}</Text>
					</Box>
				)}
				{title && <Text color={color}>├</Text>}
				<Box flexGrow={1} flexShrink={1} flexBasis={0} height={1} overflow="hidden">
					{/* wraps onto hidden lines instead of truncating (truncate would add an ellipsis) */}
					<Text color={color}>{FILL}</Text>
				</Box>
				{subtitle && (
					<Box flexShrink={0}>
						<Text color={color}>┤</Text>
						<Text color={subtitleColor ?? color}>{` ${subtitle} `}</Text>
						<Text color={color}>├</Text>
					</Box>
				)}
				<Text color={color}>─╮</Text>
			</Box>
			<Box
				borderStyle="round"
				borderTop={false}
				borderColor={color}
				flexDirection="column"
				flexGrow={1}
				paddingX={1}
				overflow="hidden"
			>
				{children}
			</Box>
		</Box>
	);
}
