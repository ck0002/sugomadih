// Input hooks. Use these instead of Ink's useInput directly:
// with the kitty keyboard protocol on (index.tsx) terminals also send key *release* events,
// which plain useInput handlers would treat as a second press.
import {useEffect, useRef} from 'react';
import {useInput, type Key} from 'ink';
import {HoldRepeater} from './holdRepeat.js';

type Handler = (input: string, key: Key) => void;

/** Like useInput, but ignores key releases. Repeats (holding an arrow) still come through. */
export function usePress(handler: Handler, options?: {isActive?: boolean}): void {
	useInput((input, key) => {
		if (key.eventType === 'release') return;
		handler(input, key);
	}, options);
}

export type HoldBinding = {
	interval: number; // ms between steps while held
	action: () => boolean; // false = couldn't act now (e.g. engine busy), retried shortly
};

/** Keys that repeat at a steady rate while held (movement). See holdRepeat.ts for how holds are detected. */
export function useHoldKeys(bindings: Record<string, HoldBinding>, enabled: boolean): void {
	const latest = useRef(bindings);
	latest.current = bindings;
	const repeater = useRef<HoldRepeater | null>(null);
	repeater.current ??= new HoldRepeater({
		intervalFor: key => latest.current[key]?.interval ?? 200,
		fire: key => latest.current[key]?.action() ?? true,
	});

	useEffect(() => {
		if (!enabled) repeater.current?.stopAll();
	}, [enabled]);
	useEffect(() => () => repeater.current?.stopAll(), []);

	useInput((input, key) => {
		if (!enabled || !(input in latest.current)) return;
		repeater.current!.handle(input, key.eventType);
	});
}
