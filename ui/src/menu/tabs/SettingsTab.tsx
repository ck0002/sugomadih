import {Box, Text} from 'ink';
import {SelectList} from '../../components/SelectList.js';
import {TYPING_SPEEDS, useSettings, type TypingSpeed} from '../../settings/settings.js';
import type {MenuTab, TabProps} from '../types.js';

const SPEEDS = Object.keys(TYPING_SPEEDS) as TypingSpeed[];
const cap = (s: string) => s[0]!.toUpperCase() + s.slice(1);

// Enter cycles the highlighted setting. Settings are saved to .dnllm-settings.json.
function SettingsTab({isActive}: TabProps) {
	const {settings, update} = useSettings();
	const rows = [
		{
			key: 'typing',
			label: `Typing speed      ‹ ${cap(settings.typingSpeed)} ›`,
			next: () => update({typingSpeed: SPEEDS[(SPEEDS.indexOf(settings.typingSpeed) + 1) % SPEEDS.length]!}),
		},
		{
			key: 'intro',
			label: `Game master intro ‹ ${settings.gmIntro ? 'On' : 'Off'} ›`,
			next: () => update({gmIntro: !settings.gmIntro}),
		},
	];
	return (
		<Box columnGap={4}>
			<SelectList entries={rows} isActive={isActive} onSelect={i => rows[i]!.next()} />
			<Box flexDirection="column">
				<Text dimColor>enter: change</Text>
				<Text dimColor>
					typing: {SPEEDS.map(s => `${s} ${Number.isFinite(TYPING_SPEEDS[s]) ? TYPING_SPEEDS[s] + ' cps' : ''}`.trim()).join(' · ')}
				</Text>
			</Box>
		</Box>
	);
}

export const settingsTab: MenuTab = {id: 'settings', label: 'SETTINGS', Component: SettingsTab};
