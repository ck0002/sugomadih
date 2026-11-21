import {useState} from 'react';
import {Box, Text} from 'ink';
import {usePress} from '../input/keys.js';
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

	usePress((_input, key) => {
		if (key.leftArrow) setActive(i => (i - 1 + TABS.length) % TABS.length);
		if (key.rightArrow) setActive(i => (i + 1) % TABS.length);
	});

	const tab = TABS[active]!;

	return (
		<Panel title="Menu" subtitle="← →" color="yellow" titleColor="yellowBright" height={height} flexShrink={0}>
			<Box marginBottom={1}>
				{TABS.map((t, i) => (
					<Text key={t.id}>
						{i > 0 && <Text color="gray"> │ </Text>}
						<Text bold={i === active} inverse={i === active} color={i === active ? 'yellowBright' : 'gray'}>
							{i === active ? ` ◆ ${t.label} ` : ` ${t.label} `}
						</Text>
					</Text>
				))}
			</Box>
			{/* key resets the tab's cursor when you switch tabs */}
			<tab.Component key={tab.id} state={state} isActive dispatch={dispatch} />
		</Panel>
	);
}
