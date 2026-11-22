import {Box, Text} from 'ink';
import {Panel} from '../components/Panel.js';
import {usePress} from '../input/keys.js';
import {useTick} from '../render/animation.js';
import {useTypewriter} from '../render/useTypewriter.js';
import {useTypingCps} from '../settings/settings.js';
import type {GameState} from '../types.js';
import {DEFEAT, GM_FRAMES, VICTORY} from './art.js';

type Props = {state: GameState; width: number; height: number; onNewGame: () => void};

// The end of a run: banner, the game master reading the epilogue, run stats. Enter = play again.
export function EndingScreen({state, width, height, onNewGame}: Props) {
	const tick = useTick();
	const ending = state.ending!;
	const victory = ending.kind === 'victory';
	const {shown, done, skip} = useTypewriter(ending.text, useTypingCps());
	const color = victory ? 'yellow' : 'red';

	usePress((input, key) => {
		if (!(key.return || input === ' ')) return;
		if (done) onNewGame();
		else skip();
	});

	const face = done ? GM_FRAMES.idle : GM_FRAMES.talking[tick % GM_FRAMES.talking.length]!;
	const {stats, story} = state;
	const chaptersDone = story.chapters.filter(c => c.status === 'done').length + (victory ? 1 : 0);

	return (
		<Box width={width} height={height} flexDirection="column" alignItems="center" justifyContent="center">
			<Text color={victory ? (tick % 8 < 4 ? 'yellowBright' : 'yellow') : 'red'}>{victory ? VICTORY : DEFEAT}</Text>
			<Panel title={`${story.title} · ${ending.title}`} color={color} width={Math.min(100, width - 4)} marginTop={1}>
				<Box columnGap={3} paddingY={1}>
					<Box flexShrink={0}>
						<Text color="magenta">{face}</Text>
					</Box>
					<Box flexDirection="column" flexGrow={1} flexShrink={1}>
						<Text>
							{shown}
							{!done && <Text color="magentaBright">▌</Text>}
						</Text>
						<Box marginTop={1} flexDirection="column">
							<Text dimColor>
								{`Chapters ${chaptersDone}/${story.chapter_count} · rooms ${stats.rooms} · enemies slain ${stats.kills} · damage dealt ${stats.damage_dealt} · turns ${stats.turns}`}
							</Text>
						</Box>
						<Box justifyContent="flex-end" marginTop={1}>
							{done ? (
								<Text color={tick % 8 < 5 ? 'magentaBright' : 'magenta'}>[enter] play again ▸   [q] quit</Text>
							) : (
								<Text dimColor>[enter] skip</Text>
							)}
						</Box>
					</Box>
				</Box>
			</Panel>
		</Box>
	);
}
