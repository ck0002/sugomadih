// Room looks. The LLM picks a theme name (engine/data/catalog.py THEMES); this maps it to colours.
// To add a theme: add it here AND to THEMES in the catalog.

export type Theme = {
	wall: string;
	door: string; // '+'
	exit: string; // '>'
	floor: string;
	water: string;
};

export const THEMES: Record<string, Theme> = {
	cellar: {wall: 'white', door: 'yellow', exit: 'magentaBright', floor: 'gray', water: 'blue'},
	crypt: {wall: 'blueBright', door: 'gray', exit: 'magentaBright', floor: 'gray', water: 'cyan'},
	cave: {wall: 'yellow', door: 'white', exit: 'magentaBright', floor: 'yellow', water: 'blue'},
	sewer: {wall: 'green', door: 'yellow', exit: 'magentaBright', floor: 'gray', water: 'greenBright'},
};

export const themeFor = (name: string | undefined): Theme => THEMES[name ?? ''] ?? THEMES['cellar']!;
