import {Box, Text} from 'ink';
import {useTick} from '../render/animation.js';

type Props = {narration: string; loading: string | null};

const SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

// The LLM's narration for the current room, or a spinner while it's writing the next one.
export function StoryText({narration, loading}: Props) {
	const tick = useTick();
	if (loading) {
		return (
			<Text color="cyan">
				{SPINNER[tick % SPINNER.length]} {loading}
			</Text>
		);
	}
	return (
		<Box>
			<Text>{narration}</Text>
		</Box>
	);
}
