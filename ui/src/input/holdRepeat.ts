// Hold-to-repeat for movement keys, at OUR rate instead of the OS key-repeat rate.
//
// Terminals normally don't report key releases. Holding a key gives: one press, then nothing for the
// OS "delay until repeat" (~0.3-0.6 s), then a fast stream of repeats. Acting on every event makes
// movement freeze, then race, then keep going after release (queued moves).
//
// Two modes, picked per key event:
// - precise: the terminal speaks the kitty keyboard protocol (eventType press/repeat/release). We fire on
//   press, then every `interval` ms until release. Linear from the very first step.
// - fallback: no release events. We fire on press (a tap = exactly one step). The hold is confirmed when
//   the first OS repeat arrives; from then on we fire every `interval` ms ourselves (the OS repeat rate
//   doesn't matter), and treat the key as released when repeats stop arriving.
//
// Pure logic (no React, injectable clock) so it can be unit tested.

export type KeyEventType = 'press' | 'repeat' | 'release' | undefined;

export type Clock = {
	now: () => number;
	setInterval: (fn: () => void, ms: number) => unknown;
	clearInterval: (handle: unknown) => void;
};

const realClock: Clock = {
	now: () => performance.now(),
	setInterval: (fn, ms) => setInterval(fn, ms),
	clearInterval: handle => clearInterval(handle as ReturnType<typeof setInterval>),
};

export const TICK_MS = 10; // how often held keys are checked
const MIN_RELEASE_MS = 150; // fallback: no repeat for this long (or 2.5x the repeat gap) = released
const MAX_INITIAL_DELAY_MS = 1000; // fallback: no first repeat within this = it was a tap

type Held = {
	precise: boolean; // got kitty event types for this key
	confirmed: boolean; // known to be held (precise press, or a repeat arrived)
	lastSeen: number; // last event for this key
	lastFire: number;
	repeatGap: number; // fallback: observed time between OS repeats
};

export type HoldRepeaterOptions = {
	intervalFor: (key: string) => number; // ms between steps while held
	fire: (key: string) => boolean; // do the action; return false if it couldn't run now (retried next tick)
	clock?: Clock;
};

export class HoldRepeater {
	private held = new Map<string, Held>();
	private timer: unknown = null;
	// Set once the terminal has sent any event type: it reports releases, so even plain presses are precise.
	private releasesSupported = false;
	private readonly clock: Clock;

	constructor(private readonly opts: HoldRepeaterOptions) {
		this.clock = opts.clock ?? realClock;
	}

	/** Feed every key event for a bound key. */
	handle(key: string, eventType: KeyEventType): void {
		const now = this.clock.now();
		if (eventType !== undefined) this.releasesSupported = true;
		if (eventType === 'release') {
			this.stop(key);
			return;
		}
		const h = this.held.get(key);
		if (!h || eventType === 'press') {
			// A fresh press (a 'press' for a key we think is held means we missed its release).
			const precise = eventType !== undefined || this.releasesSupported;
			const fired = this.opts.fire(key);
			// If the engine was busy, pretend the last step was a full interval ago so the next tick retries.
			const lastFire = fired ? now : now - this.opts.intervalFor(key);
			this.held.set(key, {precise, confirmed: precise || !fired, lastSeen: now, lastFire, repeatGap: 0});
			this.ensureTimer();
			return;
		}
		// A repeat: OS auto-repeat (fallback) or kitty 'repeat'. It only proves the key is still down.
		if (!h.precise && h.confirmed) h.repeatGap = now - h.lastSeen;
		h.confirmed = true;
		h.lastSeen = now;
		this.tick();
	}

	isHeld(key: string): boolean {
		return this.held.has(key);
	}

	stop(key: string): void {
		this.held.delete(key);
		if (this.held.size === 0 && this.timer !== null) {
			this.clock.clearInterval(this.timer);
			this.timer = null;
		}
	}

	stopAll(): void {
		for (const key of [...this.held.keys()]) this.stop(key);
	}

	/** Runs every TICK_MS while something is held. Public for tests. */
	tick(): void {
		const now = this.clock.now();
		for (const [key, h] of [...this.held]) {
			if (!h.precise) {
				const quiet = now - h.lastSeen;
				const releaseAfter = h.confirmed ? Math.max(MIN_RELEASE_MS, h.repeatGap * 2.5) : MAX_INITIAL_DELAY_MS;
				if (quiet > releaseAfter) {
					this.stop(key);
					continue;
				}
			}
			if (!h.confirmed) continue; // fallback: might be a tap, wait for the first repeat

			const interval = this.opts.intervalFor(key);
			if (now - h.lastFire < interval) continue;
			if (!this.opts.fire(key)) continue; // busy: try again next tick
			// Keep an exact cadence unless we fell behind (e.g. waited for the engine).
			h.lastFire = now - h.lastFire < interval + TICK_MS * 2 ? h.lastFire + interval : now;
		}
	}

	private ensureTimer(): void {
		if (this.timer === null) this.timer = this.clock.setInterval(() => this.tick(), TICK_MS);
	}
}
