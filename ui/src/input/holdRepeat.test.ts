import assert from 'node:assert/strict';
import {test} from 'node:test';
import {HoldRepeater, TICK_MS, type Clock, type KeyEventType} from './holdRepeat.js';

const INTERVAL = 180;

// Fake time: advance() moves the clock in TICK_MS steps and runs the repeater's timer.
function setup(opts: {busyUntil?: number} = {}) {
	let now = 0;
	let timer: (() => void) | null = null;
	const fires: number[] = [];
	const clock: Clock = {
		now: () => now,
		setInterval: fn => ((timer = fn), 1),
		clearInterval: () => (timer = null),
	};
	const repeater = new HoldRepeater({
		intervalFor: () => INTERVAL,
		fire: () => {
			if (opts.busyUntil !== undefined && now < opts.busyUntil) return false;
			fires.push(now);
			return true;
		},
		clock,
	});
	const advance = (ms: number) => {
		for (let t = 0; t < ms; t += TICK_MS) {
			now += TICK_MS;
			timer?.();
		}
	};
	const key = (type: KeyEventType) => repeater.handle('w', type);
	// OS auto-repeat: `count` repeats every `gap` ms (no event types, like Apple Terminal).
	const osRepeats = (count: number, gap: number) => {
		for (let i = 0; i < count; i++) {
			advance(gap);
			key(undefined);
		}
	};
	return {fires, advance, key, osRepeats, repeater, time: () => now};
}

test('precise (kitty): fires on press, then at a steady interval, stops on release', () => {
	const s = setup();
	s.key('press');
	s.advance(1000);
	s.key('release');
	s.advance(1000);
	assert.deepEqual(s.fires, [0, 180, 360, 540, 720, 900]);
});

test('precise: kitty repeat events do not speed it up', () => {
	const s = setup();
	s.key('press');
	for (let i = 0; i < 30; i++) {
		s.advance(30);
		s.key('repeat');
	}
	s.key('release');
	assert.equal(s.fires.length, 6); // 900 ms held -> steps at 0,180,...,900
});

test('fallback: a tap is exactly one step', () => {
	const s = setup();
	s.key(undefined);
	s.advance(2000);
	assert.deepEqual(s.fires, [0]);
	assert.equal(s.repeater.isHeld('w'), false);
});

test('fallback: hold steps at OUR interval once OS repeats start, regardless of OS repeat rate', () => {
	const s = setup();
	s.key(undefined); // press at 0
	s.advance(500); // OS "delay until repeat"
	s.key(undefined); // first repeat at 500: hold confirmed, step is overdue -> fires now
	s.osRepeats(30, 30); // fast OS repeats for 900 ms
	const gaps = s.fires.slice(2).map((t, i) => t - s.fires[i + 1]!);
	assert.equal(s.fires[0], 0);
	assert.equal(s.fires[1], 500);
	assert.ok(gaps.every(g => g === INTERVAL), `steady steps, got gaps ${gaps}`);
});

test('fallback: stops soon after OS repeats stop (no queued moves after release)', () => {
	const s = setup();
	s.key(undefined);
	s.advance(500);
	s.key(undefined);
	s.osRepeats(10, 30); // released at t=800
	const releasedAt = s.time();
	s.advance(2000);
	const after = s.fires.filter(t => t > releasedAt + 160);
	assert.deepEqual(after, []);
	assert.equal(s.repeater.isHeld('w'), false);
});

test('busy engine: the step waits instead of piling up, then the cadence resumes', () => {
	const s = setup({busyUntil: 400});
	s.key('press'); // fire refused (busy) — first step happens once free
	s.advance(1000);
	s.key('release');
	assert.ok(s.fires[0]! >= 400);
	const gaps = s.fires.slice(1).map((t, i) => t - s.fires[i]!);
	assert.ok(gaps.every(g => g === INTERVAL), `gaps ${gaps}`);
});

test('kitty terminal sending plain-text presses: precise once a release has been seen', () => {
	const s = setup();
	s.key(undefined); // first ever press: can't know yet -> tap behaviour
	s.advance(50);
	s.key('release'); // terminal reports releases
	s.advance(500);
	s.fires.length = 0;
	s.key(undefined); // plain-text press, but now trusted
	s.advance(600);
	s.key('release');
	s.advance(600);
	assert.deepEqual(s.fires.map(t => t - s.fires[0]!), [0, 180, 360, 540]);
});
