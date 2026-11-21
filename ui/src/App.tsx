import {useState} from 'react';
import {Box, Text, useInput, useWindowSize} from 'ink';
import {Panel} from './components/Panel.js';
import {Minimap} from './map/Minimap.js';
import {NearbyList} from './map/NearbyList.js';
import {MenuBox} from './menu/MenuBox.js';
import {applyMockAction} from './mock/engine.js';
import {mockState} from './mock/state.js';
import {entityAt, tileAhead} from './state.js';
import type {Action, GameState} from './types.js';
import {FirstPersonView} from './view3d/FirstPersonView.js';

const SIDE_WIDTH = 26;
const PANEL_CHROME_X = 4; // border + padding, left and right
const PANEL_CHROME_Y = 3; // border top/bottom + title row
const MINIMAP_HEIGHT = 9;

// Screen layout. Top 3/4: world (3D view + side panels). Bottom 1/4: menu.
// To add a box, drop another <Panel> into the row or column where you want it.
export function App() {
	const {columns, rows} = useWindowSize();
	const [state, setState] = useState<GameState>(mockState);
	const [message, setMessage] = useState<string>('');

	// Later: send the action to the Python engine and get new state back.
	const dispatch = (action: Action) => {
		const result = applyMockAction(state, action);
		setState(result.state);
		setMessage(result.message ?? '');
	};

	useInput(input => {
		if (input === 'w') dispatch({type: 'move', dir: 'forward'});
		if (input === 's') dispatch({type: 'move', dir: 'back'});
		if (input === 'a') dispatch({type: 'turn', dir: 'left'});
		if (input === 'd') dispatch({type: 'turn', dir: 'right'});
	});

	const menuHeight = Math.max(9, Math.floor(rows / 4));
	const worldHeight = rows - menuHeight - 1; // 1 = hint line
	const ahead = tileAhead(state);
	const facing = entityAt(state, ahead.x, ahead.y);

	return (
		<Box width={columns} height={rows} flexDirection="column">
			<Box height={worldHeight}>
				<Panel title={state.map.name + (facing ? `  ·  ahead: ${facing.name}` : '')} color="cyan" flexGrow={1}>
					<FirstPersonView
						state={state}
						width={columns - SIDE_WIDTH - PANEL_CHROME_X}
						height={worldHeight - PANEL_CHROME_Y}
					/>
				</Panel>
				<Box flexDirection="column" width={SIDE_WIDTH} flexShrink={0}>
					<Panel title="Map" flexShrink={0}>
						<Minimap state={state} width={SIDE_WIDTH - PANEL_CHROME_X} height={MINIMAP_HEIGHT} />
					</Panel>
					<Panel title="Nearby" flexGrow={1}>
						<NearbyList state={state} />
					</Panel>
				</Box>
			</Box>
			<MenuBox state={state} dispatch={dispatch} height={menuHeight} />
			<Text dimColor wrap="truncate">
				{' w/s move  a/d turn  ←/→ tab  ↑/↓ select  enter use  q quit'}
				{message && <Text color="yellow">{`   ${message}`}</Text>}
			</Text>
		</Box>
	);
}
