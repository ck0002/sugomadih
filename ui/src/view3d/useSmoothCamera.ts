import {useEffect, useRef, useState} from 'react';
import type {Camera} from './raycast.js';

const FRAME_MS = 33; // ~30 fps while gliding
const SNAP_DISTANCE = 1.5; // further than one tile (new room, teleport) = jump, don't glide

// Glides the camera to `target` over `durationMs`: position linearly, view direction along the shortest turn.
// With durationMs = the hold-to-move step, holding a key gives one continuous glide instead of tile jumps.
export function useSmoothCamera(target: Camera, durationMs: number): Camera {
	const [camera, setCamera] = useState(target);
	const current = useRef(target);

	useEffect(() => {
		const from = current.current;
		const far = Math.hypot(target.x - from.x, target.y - from.y) > SNAP_DISTANCE;
		if (durationMs <= 0 || far) {
			current.current = target;
			setCamera(target);
			return;
		}
		const start = performance.now();
		const a0 = Math.atan2(from.dirY, from.dirX);
		let turn = Math.atan2(target.dirY, target.dirX) - a0;
		turn = Math.atan2(Math.sin(turn), Math.cos(turn)); // shortest way round

		const step = () => {
			const t = Math.min(1, (performance.now() - start) / durationMs);
			const angle = a0 + turn * t;
			const next =
				t >= 1
					? target
					: {
							x: from.x + (target.x - from.x) * t,
							y: from.y + (target.y - from.y) * t,
							dirX: Math.cos(angle),
							dirY: Math.sin(angle),
						};
			current.current = next;
			setCamera(next);
			return t >= 1;
		};
		const timer = setInterval(() => step() && clearInterval(timer), FRAME_MS);
		step();
		return () => clearInterval(timer);
	}, [target.x, target.y, target.dirX, target.dirY, durationMs]);

	return camera;
}
