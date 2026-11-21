// ASCII art for the game master screen. Frames are swapped by the animation tick.

const raw = (s: TemplateStringsArray) => String.raw(s).replace(/^\n/, '').replace(/\n$/, '');

export const LOGO = raw`
 ____        _     _     __  __
|  _ \ _ __ | |   | |   |  \/  |
| | | | '_ \| |   | |   | |\/| |
| |_| | | | | |___| |___| |  | |
|____/|_| |_|_____|_____|_|  |_|
`;

// The hooded game master. Eyes and mouth are 7-character slots swapped per frame.
const frame = (eyes: string, mouth: string) =>
	[
		"         .-'''''''-.",
		"       .'   _____   '.",
		"      /    /     \\    \\",
		`     |    |${eyes}|    |`,
		`     |    |${mouth}|    |`,
		"      \\    \\_____/    /",
		"       '.  /|   |\\  .'",
		"     ____'-.|___|.-'____",
		"    /    |    |    |    \\",
		"   /_____|____|____|_____\\",
	].join('\n');

export const GM_FRAMES = {
	idle: frame(' o   o ', '   -   '),
	blink: frame(' -   - ', '   -   '),
	talking: [frame(' o   o ', '   o   '), frame(' o   o ', '   O   '), frame(' o   o ', '   -   '), frame(' o   o ', '  ___  ')],
	thinking: [frame(' -   - ', '   ~   '), frame(' -   - ', '   ~   '), frame(' .   . ', '   ~   '), frame(' -   - ', '   ~   ')],
};
