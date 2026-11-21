import {useEffect, useState} from 'react';

const MAX_TICKS_PER_SECOND = 40;

// Reveals `text` a few characters at a time at `cps` characters per second.
// Restarts whenever `text` changes. skip() shows the rest at once.
export function useTypewriter(text: string, cps: number): {shown: string; done: boolean; skip: () => void} {
	const [progress, setProgress] = useState({text, count: 0});
	const instant = !Number.isFinite(cps) || cps <= 0;
	const count = instant ? text.length : progress.text === text ? progress.count : 0;
	const done = count >= text.length;

	useEffect(() => {
		if (done) return;
		const ticksPerSecond = Math.min(cps, MAX_TICKS_PER_SECOND);
		const step = Math.max(1, Math.round(cps / ticksPerSecond));
		const timer = setTimeout(() => setProgress({text, count: Math.min(text.length, count + step)}), 1000 / ticksPerSecond);
		return () => clearTimeout(timer);
	}, [text, count, cps, done]);

	return {shown: text.slice(0, count), done, skip: () => setProgress({text, count: text.length})};
}
