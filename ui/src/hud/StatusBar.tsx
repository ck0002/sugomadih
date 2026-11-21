import {Box, Text} from 'ink';
import {HpBar} from '../components/HpBar.js';
import type {Character} from '../types.js';

const KEYS: [string, string][] = [
	['W/S', 'move'],
	['A/D', 'turn'],
	['F', 'attack'],
	['←/→', 'tab'],
	['↑/↓', 'select'],
	['⏎', 'use'],
	['Q', 'quit'],
];

// Bottom line: the player's vitals on the left, key hints on the right.
export function StatusBar({player, room, width}: {player: Character; room: number; width: number}) {
	const weapon = player.available_attacks[0]?.name ?? 'Fists';
	return (
		<Box width={width} justifyContent="space-between" paddingX={1}>
			<Text wrap="truncate">
				<Text color="red">♥ </Text>
				<HpBar hp={player.hp} max={player.total_stats.max_hp} width={12} />
				<Text dimColor>{'  AC '}</Text>
				<Text>{player.armor_class}</Text>
				<Text dimColor>{'  ⚔ '}</Text>
				<Text color="cyan">{weapon}</Text>
				{player.statuses.map(s => (
					<Text key={s.id} color="magenta">{`  ${s.name}`}</Text>
				))}
				<Text dimColor>{`  ◆ room ${room}`}</Text>
			</Text>
			<Text wrap="truncate">
				{KEYS.map(([key, label]) => (
					<Text key={key}>
						<Text inverse color="gray">{` ${key} `}</Text>
						<Text dimColor>{` ${label}  `}</Text>
					</Text>
				))}
			</Text>
		</Box>
	);
}
