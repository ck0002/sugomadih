import {Box, Text} from 'ink';
import {SelectList} from '../../components/SelectList.js';
import type {Action, GameState} from '../../types.js';
import type {MenuTab, TabProps} from '../types.js';

type Command = {label: string; action: Action; hint?: string};

function commands(state: GameState): Command[] {
	const dbg = state.debug!;
	const debug = (command: string, extra: Partial<Extract<Action, {type: 'debug'}>> = {}): Action => ({
		type: 'debug',
		command,
		...extra,
	});
	return [
		...state.story.chapters.map((c, i) => ({
			label: `Teleport → ${i + 1}. ${c.title}`,
			action: debug('goto_chapter', {chapter: i + 1}),
		})),
		{label: 'Complete objective', action: debug('complete'), hint: 'last chapter: wins the game'},
		{label: 'Kill all enemies', action: debug('kill_all')},
		{label: 'Heal party', action: debug('heal')},
		{label: `God mode        ‹ ${dbg.god ? 'On' : 'Off'} ›`, action: debug('god')},
		{label: 'Give all weapons', action: debug('give_weapons')},
		{label: 'New room (same chapter)', action: debug('reroll')},
		{label: `LLM rooms       ‹ ${dbg.llm_rooms ? 'On' : 'Off'} ›`, action: debug('llm_rooms'), hint: 'off = instant random rooms'},
		{label: 'Win now', action: debug('win')},
		{label: 'Lose now', action: debug('lose')},
	];
}

// Developer tools. Only visible when the game runs with ./play --debug.
function DebugTab({state, isActive, dispatch}: TabProps) {
	const list = commands(state);
	const dbg = state.debug!;
	return (
		<Box columnGap={3}>
			<Box width={40} flexDirection="column" flexShrink={0}>
				<SelectList
					entries={list.map(c => ({key: c.label, label: c.label}))}
					isActive={isActive}
					onSelect={i => dispatch(list[i]!.action)}
				/>
			</Box>
			<Box flexDirection="column">
				<Text color="red" bold>
					DEBUG
				</Text>
				<Text dimColor>{`pos ${dbg.player?.join(' ') ?? '-'} · room source ${dbg.room_source} · seed ${dbg.seed ?? 'random'}`}</Text>
				<Text dimColor>{`chapter ${state.story.chapter}/${state.story.chapter_count} · objective ${state.story.objective.done ? 'done' : 'open'} · run ${state.run}`}</Text>
				<Text dimColor>{`turns ${state.stats.turns} · kills ${state.stats.kills} · rooms ${state.stats.rooms}`}</Text>
				<Text dimColor>scroll ↑/↓ for more · enter: run</Text>
			</Box>
		</Box>
	);
}

export const debugTab: MenuTab = {id: 'debug', label: 'DEBUG', Component: DebugTab, visible: state => state.debug !== null};
