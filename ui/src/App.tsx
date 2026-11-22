import {useState} from 'react';
import {Box, useWindowSize} from 'ink';
import {useEngine} from './bridge/useEngine.js';
import {Panel} from './components/Panel.js';
import {EndingScreen} from './gm/EndingScreen.js';
import {GameMasterScreen} from './gm/GameMasterScreen.js';
import {useHoldKeys, usePress} from './input/keys.js';
import {StatusBar} from './hud/StatusBar.js';
import {Minimap} from './map/Minimap.js';
import {NearbyList} from './map/NearbyList.js';
import {MenuBox} from './menu/MenuBox.js';
import {MOVE_SPEEDS, useSettings} from './settings/settings.js';
import {entityAt, tileAhead} from './state.js';
import {LogText} from './story/LogText.js';
import {QuestPanel} from './story/QuestPanel.js';
import {StoryText} from './story/StoryText.js';
import {FirstPersonView} from './view3d/FirstPersonView.js';

const SIDE_WIDTH = 36;
const PANEL_CHROME_X = 4; // border + padding, left and right
const PANEL_CHROME_Y = 2; // top border (with title) + bottom border
const MINIMAP_HEIGHT = 9;
const LOG_LINES = 5;

// Flow: game master screen while the LLM builds a room -> game master intro (typed) -> the game.
// Game layout: top 3/4 is the world (3D view + log, side panels), bottom 1/4 the menu, then the status bar.
// To add a box, drop another <Panel> into the row or column where you want it.
export function App() {
	const {columns, rows} = useWindowSize();
	const {state, narration, narrating, message, loading, dispatch, busy} = useEngine();
	const {settings} = useSettings();
	const [introSeen, setIntroSeen] = useState(''); // run:room whose intro was dismissed
	const roomKey = state ? `${state.run}:${state.room}` : '';
	const showIntro = Boolean(state && settings.gmIntro && roomKey !== introSeen);

	const playing = Boolean(state && !loading && !showIntro && !state.ending);
	const step = MOVE_SPEEDS[settings.moveSpeed];

	// Movement repeats at a steady `step` while held (input/holdRepeat.ts). An action only goes out when
	// the previous one has been answered, so moves never pile up and stop the moment the key is let go.
	const act = (action: Parameters<typeof dispatch>[0]) => () => {
		if (busy()) return false;
		dispatch(action);
		return true;
	};
	useHoldKeys(
		{
			w: {interval: step, action: act({type: 'move', dir: 'forward'})},
			s: {interval: step, action: act({type: 'move', dir: 'back'})},
			a: {interval: step * 1.4, action: act({type: 'turn', dir: 'left'})},
			d: {interval: step * 1.4, action: act({type: 'turn', dir: 'right'})},
		},
		playing,
	);
	usePress(input => {
		if (playing && input === 'f' && !busy()) dispatch({type: 'attack', attack: 0}); // default attack (first weapon)
	});

	if (!state || loading) {
		const text = loading ?? message;
		return <GameMasterScreen mode="thinking" width={columns} height={rows} message={text} showLogo={!state} />;
	}
	if (state.ending) {
		return state.ending.text ? (
			<EndingScreen state={state} width={columns} height={rows} onNewGame={() => dispatch({type: 'new_game'})} />
		) : (
			<GameMasterScreen mode="thinking" width={columns} height={rows} message="The game master writes the ending..." showLogo={false} />
		);
	}
	if (showIntro) {
		return (
			<GameMasterScreen
				mode="speaking"
				width={columns}
				height={rows}
				chapter={`CHAPTER ${state.story.chapter} OF ${state.story.chapter_count} · ${state.story.chapter_title}`}
				roomName={state.map.name}
				goal={state.story.objective.text}
				text={narration}
				onContinue={() => setIntroSeen(roomKey)}
			/>
		);
	}

	const menuHeight = Math.max(9, Math.floor(rows / 4));
	const worldHeight = rows - menuHeight - 1; // 1 = status bar
	const viewHeight = worldHeight - (LOG_LINES + PANEL_CHROME_Y);
	const player = state.party[0]!;

	const ahead = tileAhead(state);
	const facing = entityAt(state, ahead.x, ahead.y);
	const atExit = state.map.tiles[ahead.y]?.[ahead.x] === '>';
	const enemyAhead = facing?.kind === 'character' && facing.hostile;
	const aheadText =
		facing?.kind === 'character'
			? `${facing.name} ${facing.hp}/${facing.total_stats.max_hp} hp` + facing.statuses.map(s => ` · ${s.name}`).join('')
			: facing
				? facing.name
				: atExit
					? 'the exit ▸'
					: undefined;

	return (
		<Box width={columns} height={rows} flexDirection="column">
			<Box height={worldHeight}>
				<Box flexDirection="column" flexGrow={1}>
					<Panel
						title={`${state.story.chapter}/${state.story.chapter_count} · ${state.map.name}`}
						subtitle={aheadText && `ahead: ${aheadText}`}
						color={enemyAhead ? 'red' : 'cyan'}
						titleColor={enemyAhead ? 'redBright' : 'cyanBright'}
						subtitleColor={enemyAhead ? 'redBright' : atExit ? 'magentaBright' : undefined}
						height={viewHeight}
					>
						<FirstPersonView
							state={state}
							glideMs={settings.smoothCamera ? step : 0}
							width={columns - SIDE_WIDTH - PANEL_CHROME_X}
							height={viewHeight - PANEL_CHROME_Y}
						/>
					</Panel>
					<Panel title="Log" color="gray" height={LOG_LINES + PANEL_CHROME_Y} flexShrink={0}>
						<LogText log={state.log} fresh={state.log_fresh} lines={LOG_LINES} />
					</Panel>
				</Box>
				<Box flexDirection="column" width={SIDE_WIDTH} flexShrink={0}>
					<Panel title="Map" color="blue" titleColor="blueBright" flexShrink={0}>
						<Minimap state={state} width={SIDE_WIDTH - PANEL_CHROME_X} height={MINIMAP_HEIGHT} />
					</Panel>
					<Panel title="Quest" color="yellow" titleColor="yellowBright" flexShrink={0}>
						<QuestPanel story={state.story} />
					</Panel>
					<Panel title="Game Master" color="magenta" titleColor="magentaBright" flexGrow={1}>
						<StoryText narration={narration} narrating={narrating} />
					</Panel>
					<Panel title="Nearby" color="green" titleColor="greenBright" flexShrink={0}>
						<NearbyList state={state} />
					</Panel>
				</Box>
			</Box>
			<MenuBox state={state} dispatch={dispatch} height={menuHeight} />
			<StatusBar player={player} state={state} width={columns} />
		</Box>
	);
}
