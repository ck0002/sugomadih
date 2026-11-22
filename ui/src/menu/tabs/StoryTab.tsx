import {useState} from 'react';
import {Box, Text} from 'ink';
import {SelectList} from '../../components/SelectList.js';
import type {MenuTab, TabProps} from '../types.js';

// The campaign so far: chapters on the left, the journal of the highlighted chapter on the right.
function StoryTab({state, isActive}: TabProps) {
	const {story} = state;
	const [index, setIndex] = useState(story.chapter - 1);
	const chapter = story.chapters[index];
	const entries = story.journal.filter(j => j.chapter === index + 1);

	return (
		<Box columnGap={3}>
			<Box width={34} flexDirection="column" flexShrink={0}>
				<SelectList
					entries={story.chapters.map((c, i) => ({
						key: c.title,
						label: `${c.status === 'done' ? '●' : c.status === 'current' ? '◆' : '○'} ${i + 1}. ${c.status === 'locked' ? '???' : c.title}`,
						color: c.status === 'done' ? 'green' : c.status === 'locked' ? 'gray' : undefined,
					}))}
					isActive={isActive}
					onHighlight={setIndex}
					initialIndex={story.chapter - 1}
				/>
			</Box>
			<Box flexDirection="column" flexShrink={1}>
				{chapter?.status === 'locked' ? (
					<Text dimColor>Not yet written.</Text>
				) : (
					<>
						<Text bold color="yellow">
							{chapter?.title}
						</Text>
						<Text dimColor>{`Goal: ${chapter?.objective}`}</Text>
						{entries.slice(-4).map((e, i) => (
							<Text key={i} wrap="truncate-end">
								{e.text}
							</Text>
						))}
					</>
				)}
			</Box>
		</Box>
	);
}

export const storyTab: MenuTab = {id: 'story', label: 'STORY', Component: StoryTab};
