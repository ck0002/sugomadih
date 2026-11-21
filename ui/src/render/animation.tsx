// Shared animation clock + helpers for picking the current frame of an entity.
import {createContext, useContext, useEffect, useState, type ReactNode} from 'react';
import type {Animations} from '../types.js';

export const FPS = 8;

const TickContext = createContext(0);

// Wrap the app in this once. Only components that call useTick() re-render on each tick.
export function AnimationClock({fps = FPS, children}: {fps?: number; children: ReactNode}) {
	const [tick, setTick] = useState(0);
	useEffect(() => {
		const timer = setInterval(() => setTick(t => t + 1), 1000 / fps);
		return () => clearInterval(timer);
	}, [fps]);
	return <TickContext value={tick}>{children}</TickContext>;
}

export const useTick = () => useContext(TickContext);

type Animated = {id: string; art: Animations; animation: string};

// Frames of the animation that's playing now (falls back to idle).
export function framesOf(entity: Animated): string[] {
	return entity.art[entity.animation] ?? entity.art['idle'] ?? [];
}

// The frame to show at this tick. Each entity is offset by its id so they don't all move in sync.
export function frameAt(entity: Animated, tick: number): string {
	const frames = framesOf(entity);
	if (frames.length === 0) return '';
	return frames[(tick + offsetFor(entity.id)) % frames.length]!;
}

// Size of the biggest frame, so the sprite doesn't jump around as frames change.
export function frameBox(frames: string[]): {width: number; height: number} {
	let width = 0;
	let height = 0;
	for (const f of frames) {
		const lines = f.split('\n');
		height = Math.max(height, lines.length);
		for (const l of lines) width = Math.max(width, l.length);
	}
	return {width, height};
}

function offsetFor(id: string): number {
	let h = 0;
	for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
	return h % 997;
}
