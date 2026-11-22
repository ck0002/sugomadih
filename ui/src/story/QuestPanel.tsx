import {Box, Text} from 'ink';
import type {StoryState} from '../types.js';

// Where you are in the story and what to do next.
export function QuestPanel({story}: {story: StoryState}) {
	const {objective} = story;
	return (
		<Box flexDirection="column">
			<Text>
				<Text dimColor>{`Chapter ${story.chapter}/${story.chapter_count} `}</Text>
				<Text bold color="yellow">
					{story.chapter_title}
				</Text>
			</Text>
			<Text color={objective.done ? 'green' : undefined}>
				{objective.done ? '☑ ' : '☐ '}
				{objective.text}
			</Text>
			<Text>
				{story.chapters.map((c, i) => (
					<Text key={i} color={c.status === 'done' ? 'green' : c.status === 'current' ? 'yellowBright' : 'gray'}>
						{c.status === 'done' ? '●' : c.status === 'current' ? '◆' : '○'}
						{i < story.chapters.length - 1 ? '─' : ''}
					</Text>
				))}
				<Text color={story.exit_open ? 'magentaBright' : 'gray'}>{story.exit_open ? '  exit open ▸' : '  exit sealed'}</Text>
			</Text>
		</Box>
	);
}
