import {Box, Text} from 'ink';
import {useTick} from '../render/animation.js';
import {useTypewriter} from '../render/useTypewriter.js';
import {useTypingCps} from '../settings/settings.js';

type Props = {narration: string; narrating: boolean};

// The game master's latest words: room intro, then a retelling after every fight action. Typed out.
export function StoryText({narration, narrating}: Props) {
	const tick = useTick();
	const {shown, done} = useTypewriter(narration, useTypingCps());
	return (
		<Box flexDirection="column">
			<Text>
				{shown}
				{!done && <Text color="magentaBright">▌</Text>}
			</Text>
			{narrating && done && (
				<Text color="magenta" dimColor>
					{'✎ the game master writes' + '.'.repeat((tick % 4) + 1)}
				</Text>
			)}
		</Box>
	);
}
