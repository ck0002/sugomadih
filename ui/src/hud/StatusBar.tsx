import {Box, Text} from 'ink';
import {HpBar} from '../components/HpBar.js';
import type {Character, GameState} from '../types.js';

const KEYS: [string, string][] = [ // keep it short: shares the line with the vitals
	['W/S', 'move'],
	['A/D', 'turn'],
	['F', 'attack'],
	['←/→', 'tab'],
	['↑/↓', 'select'],
	['⏎', 'use'],
	['Q', 'quit'],
];

// Bottom line: the player's vitals on the left, key hints on the right.
export function StatusBar({player, state, width}: {player: Character; state: GameState; width: number}) {
	const weapon = player.available_attacks[0]?.name ?? 'Fists';
	const dbg = state.debug;
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
				<Text dimColor>{`  ◆ ch ${state.story.chapter}/${state.story.chapter_count}`}</Text>
				{dbg && (
					<Text>
						<Text inverse color="red">
							{' DEBUG '}
						</Text>
						<Text color="red">{` ${dbg.player?.slice(0, 2).join(',') ?? ''}${dbg.god ? ' god' : ''}${dbg.room_source === 'fallback' ? ' rnd' : ''}`}</Text>
					</Text>
				)}
			</Text>
			<Text wrap="truncate">
				{(dbg ? KEYS.filter(([k]) => ['W/S', 'A/D', 'F', 'Q'].includes(k)) : KEYS).map(([key, label]) => (
					<Text key={key}>
						<Text inverse color="gray">{` ${key} `}</Text>
						<Text dimColor>{` ${label}  `}</Text>
					</Text>
				))}
			</Text>
		</Box>
	);
}
