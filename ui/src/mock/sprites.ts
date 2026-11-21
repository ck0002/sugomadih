// Sprite animations for the mock entities.
// Each sprite is {animationName: frames[]}. Frames play at FPS (render/animation.tsx) and loop,
// so 16 frames is a 2 s loop. Use hold() to keep a pose for several frames.
import type {Animations} from '../types.js';

// Write frames as raw template strings so backslashes don't need escaping.
// The first and last newline are dropped, so frames can start on their own line.
const art = (s: TemplateStringsArray) => String.raw(s).replace(/^\n/, '').replace(/\n$/, '');

const hold = (frame: string, n: number): string[] => Array<string>(n).fill(frame);

// Copy of `frame` with one character replaced (pads short lines). Good for blinks, glints, bubbles.
function put(frame: string, row: number, col: number, ch: string): string {
	const lines = frame.split('\n');
	while (lines.length <= row) lines.push('');
	lines[row] = lines[row]!.padEnd(col).slice(0, col) + ch + lines[row]!.slice(col + 1);
	return lines.join('\n');
}

// ---- characters -------------------------------------------------------------

const goblin = art`
 ,   ,
(o\_/o)
 \ ^ /
/|===|\
 /   \
`;
const goblinEars = put(put(goblin, 0, 1, '.'), 0, 5, '.');
const goblinBlink = put(put(goblin, 1, 1, '-'), 1, 5, '-');
const goblinRaise = art`
 ,   ,   |
(o\_/o)  |
 \ ^ / __+
/|===|/
 /   \
`;
const goblinSnarl = art`
 ,   , \
(>\_/<) \
 \ O /   +
/|===|--'
 /   \
`;
const goblinStab = art`
 ,   ,
(>\_/<)
 \ O /
/|===|---+--
 /   \
`;

const merchant = art`
  ___
 (o o)
__\=/__
| [$] |
 |   |
`;
const merchantBlink = put(put(merchant, 1, 2, '-'), 1, 4, '-');
const merchantToss = (row: number) => put(put(merchant, 3, 3, ' '), row, 8, '$');

const player = art`
 o
/|\
/ \
`;
const playerShift = art`
 o
/|\
 |\
`;

const brena = art`
 o
<|>
/ \
`;

export const SPRITES = {
	goblin: {
		idle: [...hold(goblin, 8), ...hold(goblinEars, 2), ...hold(goblin, 6), ...hold(goblinBlink, 2), ...hold(goblin, 2)],
		attack: [...hold(goblin, 2), ...hold(goblinRaise, 4), ...hold(goblinSnarl, 2), ...hold(goblinStab, 5), ...hold(goblin, 2)],
	},
	merchant: {
		idle: [
			...hold(merchant, 10),
			...hold(merchantBlink, 2),
			...hold(merchant, 4),
			merchantToss(3),
			merchantToss(2),
			merchantToss(1),
			merchantToss(0),
			merchantToss(0),
			merchantToss(1),
			merchantToss(2),
			merchantToss(3),
		],
	},
	player: {
		idle: [...hold(player, 12), ...hold(playerShift, 4)],
	},
	brena: {
		idle: [
			...hold(brena, 10),
			...hold(put(brena, 0, 3, '♪'), 3),
			...hold(put(brena, 0, 4, '♫'), 3),
			...hold(put(brena, 0, 3, '♪'), 2),
			...hold(brena, 2),
		],
	},

	// ---- items ----------------------------------------------------------------

	sword: (() => {
		const f = art`
  /\
  ||
  ||
 -++-
  ||
`;
		return {idle: [...hold(f, 10), ...hold(put(f, 0, 3, '*'), 2), ...hold(put(f, 1, 3, '*'), 2), ...hold(put(f, 2, 3, '*'), 2)]};
	})(),
	potion: (() => {
		const f = art`
 _
| |
/ \
\_/
`;
		return {idle: [...hold(f, 10), ...hold(put(f, 3, 1, 'o'), 2), ...hold(put(f, 2, 1, 'o'), 2), ...hold(put(f, 1, 1, '°'), 2)]};
	})(),
	amulet: (() => {
		const f = art`
 .-.
(o o)
 |=|
`;
		return {idle: [...hold(f, 14), ...hold(put(put(f, 1, 1, '-'), 1, 3, '-'), 2)]};
	})(),
	key: (() => {
		const f = art`
 _
(_)=+=
`;
		return {idle: [...hold(f, 10), ...hold(put(f, 0, 3, '*'), 2), ...hold(put(f, 0, 5, '*'), 2), ...hold(put(f, 0, 6, '*'), 2)]};
	})(),
} satisfies Record<string, Animations>;
