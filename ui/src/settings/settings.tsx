// Player settings, shared through context and saved to .dnllm-settings.json in the repo root.
// To add a setting: add it to Settings + DEFAULTS, then a row in menu/tabs/SettingsTab.tsx.
import {readFileSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {createContext, useCallback, useContext, useState, type ReactNode} from 'react';
import {REPO_ROOT} from '../paths.js';

// Characters per second for typing animations.
export const TYPING_SPEEDS = {slow: 25, normal: 50, fast: 110, instant: Infinity} as const;
export type TypingSpeed = keyof typeof TYPING_SPEEDS;

// Milliseconds per step while a movement key is held (turning is a bit slower).
export const MOVE_SPEEDS = {slow: 260, normal: 180, fast: 120} as const;
export type MoveSpeed = keyof typeof MOVE_SPEEDS;

export type Settings = {
	typingSpeed: TypingSpeed;
	gmIntro: boolean; // show the game master's intro before each room
	moveSpeed: MoveSpeed;
	smoothCamera: boolean; // glide the 3D view between tiles instead of jumping
};

const DEFAULTS: Settings = {typingSpeed: 'fast', gmIntro: true, moveSpeed: 'normal', smoothCamera: true};
const FILE = join(REPO_ROOT, '.dnllm-settings.json');

function load(): Settings {
	try {
		return {...DEFAULTS, ...(JSON.parse(readFileSync(FILE, 'utf8')) as Partial<Settings>)};
	} catch {
		return DEFAULTS;
	}
}

type Ctx = {settings: Settings; update: (changes: Partial<Settings>) => void};
const SettingsContext = createContext<Ctx>({settings: DEFAULTS, update: () => {}});

export function SettingsProvider({children}: {children: ReactNode}) {
	const [settings, setSettings] = useState<Settings>(load);
	const update = useCallback((changes: Partial<Settings>) => {
		setSettings(prev => {
			const next = {...prev, ...changes};
			try {
				writeFileSync(FILE, JSON.stringify(next, null, 2));
			} catch {
				// not being able to save settings shouldn't break the game
			}
			return next;
		});
	}, []);
	return <SettingsContext value={{settings, update}}>{children}</SettingsContext>;
}

// ./play --fast (dev): skip intros and typing for this session without touching the saved settings.
const FAST = process.env['DNLLM_FAST'] === '1';

export const useSettings = () => {
	const ctx = useContext(SettingsContext);
	return FAST ? {...ctx, settings: {...ctx.settings, gmIntro: false, typingSpeed: 'instant' as const}} : ctx;
};
export const useTypingCps = () => TYPING_SPEEDS[useSettings().settings.typingSpeed];
