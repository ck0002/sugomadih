import {useState} from 'react';
import {Box, Text} from 'ink';
import {usePress} from '../input/keys.js';

export type ListEntry = {key: string; label: string; color?: string};

type Props = {
	entries: ListEntry[];
	isActive: boolean; // only the focused list reacts to keys
	onHighlight?: (index: number) => void;
	onSelect?: (index: number) => void;
	maxVisible?: number; // scroll when there are more entries than this
	initialIndex?: number;
};

// Up/down to move, enter to pick. Reused by every menu tab.
export function SelectList({entries, isActive, onHighlight, onSelect, maxVisible = 6, initialIndex = 0}: Props) {
	const [index, setIndex] = useState(initialIndex);

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

	// Keep the cursor visible: show a window of maxVisible entries around it.
	const start = Math.max(0, Math.min(index - Math.floor(maxVisible / 2), entries.length - maxVisible));
	const visible = entries.slice(start, start + maxVisible);
	return (
		<Box flexDirection="column">
			{visible.map((entry, j) => {
				const i = start + j;
				const more = (j === 0 && start > 0) || (j === visible.length - 1 && start + maxVisible < entries.length);
				return (
					<Text key={entry.key} color={i === index ? 'yellow' : entry.color} wrap="truncate">
						{i === index ? '► ' : more ? (j === 0 ? '↑ ' : '↓ ') : '  '}
						{entry.label}
					</Text>
				);
			})}
		</Box>
	);
}
