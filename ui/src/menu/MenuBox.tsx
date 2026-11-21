import {useState} from 'react';
import {Box, Text, useInput} from 'ink';
import {Panel} from '../components/Panel.js';
import type {Action, GameState} from '../types.js';
import {TABS} from './tabs/index.js';

type Props = {
	state: GameState;
	dispatch: (action: Action) => void;
	height: number;
};

// Bottom menu: tab bar (left/right to switch) + the active tab's content.
export function MenuBox({state, dispatch, height}: Props) {
	const [active, setActive] = useState(0);

	useInput((_input, key) => {
		if (key.leftArrow) setActive(i => (i - 1 + TABS.length) % TABS.length);
		if (key.rightArrow) setActive(i => (i + 1) % TABS.length);
	});

	const tab = TABS[active]!;

	return (
		<Panel height={height} flexShrink={0}>
			<Box columnGap={2} marginBottom={1}>
				{TABS.map((t, i) => (
					<Text key={t.id} bold={i === active} inverse={i === active} color={i === active ? 'yellow' : 'gray'}>
						{` ${t.label} `}
					</Text>
				))}
			</Box>
			{/* key resets the tab's cursor when you switch tabs */}
			<tab.Component key={tab.id} state={state} isActive dispatch={dispatch} />
		</Panel>
	);
}
