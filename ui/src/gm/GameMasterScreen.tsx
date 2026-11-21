import {Box, Text} from 'ink';
import {usePress} from '../input/keys.js';
import {Panel} from '../components/Panel.js';
import {useTick} from '../render/animation.js';
import {useTypewriter} from '../render/useTypewriter.js';
import {useTypingCps} from '../settings/settings.js';
import {GM_FRAMES, LOGO} from './art.js';

const SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

type Props =
	| {mode: 'thinking'; width: number; height: number; message: string; showLogo: boolean}
	| {mode: 'speaking'; width: number; height: number; room: number; roomName: string; text: string; onContinue: () => void};

// Full-screen "the game master speaks" card, shown before every room (and while the LLM is working).
export function GameMasterScreen(props: Props) {
	const {width, height} = props;
	const boxWidth = Math.min(96, width - 4);
	return (
		<Box width={width} height={height} flexDirection="column" alignItems="center" justifyContent="center">
			{props.mode === 'thinking' && props.showLogo && (
				<Box marginBottom={1}>
					<Text color="magentaBright">{LOGO}</Text>
				</Box>
			)}
			<Panel title="The Game Master" color="magenta" titleColor="magentaBright" width={boxWidth} minHeight={14}>
				{props.mode === 'thinking' ? <Thinking message={props.message} /> : <Speaking {...props} />}
			</Panel>
		</Box>
	);
}

function Thinking({message}: {message: string}) {
	const tick = useTick();
	return (
		<Box columnGap={3} paddingY={1}>
			<Box flexShrink={0}>
				<Text color="magenta">{GM_FRAMES.thinking[Math.floor(tick / 3) % GM_FRAMES.thinking.length]}</Text>
			</Box>
			<Box flexDirection="column" justifyContent="center">
				<Text color="cyan">
					{SPINNER[tick % SPINNER.length]} {message}
				</Text>
			</Box>
		</Box>
	);
}

function Speaking({room, roomName, text, onContinue}: {room: number; roomName: string; text: string; onContinue: () => void}) {
	const tick = useTick();
	const {shown, done, skip} = useTypewriter(text, useTypingCps());

	usePress((input, key) => {
		if (!(key.return || input === ' ')) return;
		if (done) onContinue();
		else skip();
	});

	const face = done
		? tick % 24 < 2
			? GM_FRAMES.blink
			: GM_FRAMES.idle
		: GM_FRAMES.talking[Math.floor(tick / 1) % GM_FRAMES.talking.length]!;

	return (
		<Box columnGap={3} paddingY={1}>
			<Box flexShrink={0}>
				<Text color="magenta">{face}</Text>
			</Box>
			<Box flexDirection="column" flexGrow={1} flexShrink={1}>
				<Text dimColor>{`ROOM ${room}`}</Text>
				<Text bold color="yellow">
					{roomName}
				</Text>
				<Box marginTop={1} flexGrow={1}>
					<Text>
						{shown}
						{!done && <Text color="magentaBright">▌</Text>}
					</Text>
				</Box>
				<Box justifyContent="flex-end" marginTop={1}>
					{done ? (
						<Text color={tick % 8 < 5 ? 'magentaBright' : 'magenta'}>[enter] enter the room ▸</Text>
					) : (
						<Text dimColor>[enter] skip</Text>
					)}
				</Box>
			</Box>
		</Box>
	);
}
