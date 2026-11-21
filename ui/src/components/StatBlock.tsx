import {Box, Text} from 'ink';
import type {Stats} from '../types.js';

const LABELS: [keyof Stats, string][] = [
	['strength', 'STR'],
	['dexterity', 'DEX'],
	['constitution', 'CON'],
	['intelligence', 'INT'],
	['wisdom', 'WIS'],
	['charisma', 'CHA'],
	['max_hp', 'HP'],
];

type Props = {
	stats: Stats;
	buffs?: boolean; // show as +2 / -1 and hide zeros (for item buffs)
};

export function StatBlock({stats, buffs = false}: Props) {
	const shown = LABELS.filter(([k]) => !buffs || stats[k] !== 0);
	if (shown.length === 0) return <Text dimColor>no buffs</Text>;

	return (
		<Box flexWrap="wrap" columnGap={2}>
			{shown.map(([k, label]) => {
				const v = stats[k];
				const text = buffs ? (v > 0 ? `+${v}` : `${v}`) : `${v}`;
				return (
					<Text key={k}>
						<Text dimColor>{label}</Text> <Text color={buffs ? (v > 0 ? 'green' : 'red') : undefined}>{text}</Text>
					</Text>
				);
			})}
		</Box>
	);
}
