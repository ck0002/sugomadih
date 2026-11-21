import {Box, Text, useInput, useWindowSize} from 'ink';
import {useEngine} from './bridge/useEngine.js';
import {Panel} from './components/Panel.js';
import {Minimap} from './map/Minimap.js';
import {NearbyList} from './map/NearbyList.js';
import {MenuBox} from './menu/MenuBox.js';
import {useTick} from './render/animation.js';
import {entityAt, tileAhead} from './state.js';
import {StoryText} from './story/StoryText.js';
import {FirstPersonView} from './view3d/FirstPersonView.js';

const SIDE_WIDTH = 34;
const PANEL_CHROME_X = 4; // border + padding, left and right
const PANEL_CHROME_Y = 3; // border top/bottom + title row
const MINIMAP_HEIGHT = 9;

// Screen layout. Top 3/4: world (3D view + side panels). Bottom 1/4: menu.
// To add a box, drop another <Panel> into the row or column where you want it.
export function App() {
	const {columns, rows} = useWindowSize();
	const {state, narration, message, loading, dispatch} = useEngine();

	useInput(input => {
		if (loading || !state) return; // don't queue moves while the next room is being made
		if (input === 'w') dispatch({type: 'move', dir: 'forward'});
		if (input === 's') dispatch({type: 'move', dir: 'back'});
		if (input === 'a') dispatch({type: 'turn', dir: 'left'});
		if (input === 'd') dispatch({type: 'turn', dir: 'right'});
	});

	if (!state) return <LoadingScreen width={columns} height={rows} text={loading ?? message} />;

	const menuHeight = Math.max(9, Math.floor(rows / 4));
	const worldHeight = rows - menuHeight - 1; // 1 = hint line
	const ahead = tileAhead(state);
	const facing = entityAt(state, ahead.x, ahead.y);
	const atExit = state.map.tiles[ahead.y]?.[ahead.x] === '>';
	const title = `Room ${state.room}: ${state.map.name}` + (facing ? `  ·  ahead: ${facing.name}` : atExit ? '  ·  ahead: exit' : '');

	return (
		<Box width={columns} height={rows} flexDirection="column">
			<Box height={worldHeight}>
				<Panel title={title} color="cyan" flexGrow={1}>
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
					<Panel title="Story" color="magenta" flexGrow={1}>
						<StoryText narration={narration} loading={loading} />
					</Panel>
					<Panel title="Nearby" flexShrink={0}>
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

function LoadingScreen({width, height, text}: {width: number; height: number; text: string}) {
	const tick = useTick();
	return (
		<Box width={width} height={height} alignItems="center" justifyContent="center">
			<Text color="cyan">
				{'⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'[tick % 10]} {text}
			</Text>
		</Box>
	);
}
