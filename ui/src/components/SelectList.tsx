import {useState} from 'react';
import {Box, Text} from 'ink';
import {usePress} from '../input/keys.js';

export type ListEntry = {key: string; label: string; color?: string};

type Props = {
	entries: ListEntry[];
	isActive: boolean; // only the focused list reacts to keys
	onHighlight?: (index: number) => void;
	onSelect?: (index: number) => void;
};

// Up/down to move, enter to pick. Reused by every menu tab.
export function SelectList({entries, isActive, onHighlight, onSelect}: Props) {
	const [index, setIndex] = useState(0);

	const move = (next: number) => {
		setIndex(next);
		onHighlight?.(next);
	};

	usePress(
		(_input, key) => {
			if (entries.length === 0) return;
			if (key.upArrow) move((index - 1 + entries.length) % entries.length);
			if (key.downArrow) move((index + 1) % entries.length);
			if (key.return) onSelect?.(index);
		},
		{isActive},
	);

	if (entries.length === 0) return <Text dimColor>(nothing here)</Text>;

	return (
		<Box flexDirection="column">
			{entries.map((entry, i) => (
				<Text key={entry.key} color={i === index ? 'yellow' : entry.color}>
					{i === index ? '► ' : '  '}
					{entry.label}
				</Text>
			))}
		</Box>
	);
}
