// First-person ASCII renderer (classic grid raycaster).
// Pure function: tiles + camera + sprites in, a grid of Cells out. No React here.
import type {Cell} from '../render/CellGrid.js';

export type Camera = {x: number; y: number; dirX: number; dirY: number};

export type Sprite = {
	x: number; // world position (tile centre = n + 0.5)
	y: number;
	art: string; // ASCII art, spaces are transparent
	glyph: string; // drawn instead of the art when far away
	color: string;
	height: number; // in world units, 1 = wall height
};

const PLANE = Math.tan((66 / 2) * (Math.PI / 180)); // 66° field of view
const CHAR_ASPECT = 2; // a terminal cell is about twice as tall as it is wide
const MAX_ART_SCALE = 3; // stop tiny art from turning into giant blobs up close

// Tiles that are solid for rendering, and their colour.
const WALL_COLORS: Record<string, string> = {'#': 'white', '+': 'yellow'};
const WALL_SHADES = ['█', '▓', '▒', '░']; // near -> far

export function renderScene(tiles: string[], cam: Camera, sprites: Sprite[], width: number, height: number): Cell[][] {
	const W = Math.max(1, width);
	const H = Math.max(1, height);
	const grid: Cell[][] = Array.from({length: H}, () => Array.from({length: W}, () => ({char: ' '})));
	const zBuffer = new Array<number>(W).fill(Infinity);

	const planeX = -cam.dirY * PLANE; // camera plane points to the right of the view direction
	const planeY = cam.dirX * PLANE;
	const scale = W / (2 * PLANE * CHAR_ASPECT); // world units -> rows at distance 1
	const horizon = H / 2;
	const tileAt = (x: number, y: number) => tiles[Math.floor(y)]?.[Math.floor(x)];
	const rayDir = (col: number) => {
		const cameraX = (2 * (col + 0.5)) / W - 1;
		return [cam.dirX + planeX * cameraX, cam.dirY + planeY * cameraX] as const;
	};

	// Floor: work out which tile each cell below the horizon looks at.
	for (let y = Math.ceil(horizon); y < H; y++) {
		const dist = (0.5 * scale) / (y + 0.5 - horizon);
		for (let x = 0; x < W; x++) {
			const [rx, ry] = rayDir(x);
			const fx = cam.x + rx * dist;
			const fy = cam.y + ry * dist;
			grid[y]![x] = floorCell(tileAt(fx, fy), fx, fy, dist);
		}
	}

	// Walls: one ray per column (DDA).
	for (let x = 0; x < W; x++) {
		const [rx, ry] = rayDir(x);
		let mapX = Math.floor(cam.x);
		let mapY = Math.floor(cam.y);
		const deltaX = rx === 0 ? Infinity : Math.abs(1 / rx);
		const deltaY = ry === 0 ? Infinity : Math.abs(1 / ry);
		const stepX = rx < 0 ? -1 : 1;
		const stepY = ry < 0 ? -1 : 1;
		let sideX = rx < 0 ? (cam.x - mapX) * deltaX : (mapX + 1 - cam.x) * deltaX;
		let sideY = ry < 0 ? (cam.y - mapY) * deltaY : (mapY + 1 - cam.y) * deltaY;
		let side = 0;
		let tile: string | undefined;

		for (let i = 0; i < 64; i++) {
			if (sideX < sideY) {
				sideX += deltaX;
				mapX += stepX;
				side = 0;
			} else {
				sideY += deltaY;
				mapY += stepY;
				side = 1;
			}
			tile = tiles[mapY]?.[mapX];
			if (tile === undefined || tile in WALL_COLORS) break;
		}

		const dist = side === 0 ? sideX - deltaX : sideY - deltaY;
		zBuffer[x] = dist;
		const top = Math.max(0, Math.round(horizon - (0.5 * scale) / dist));
		const bottom = Math.min(H - 1, Math.round(horizon + (0.5 * scale) / dist) - 1);
		// Shade by distance, and make one wall orientation a step darker so corners read.
		const shade = Math.min(WALL_SHADES.length - 1, shadeIndex(dist) + side);
		const cell: Cell = {char: WALL_SHADES[shade]!, color: WALL_COLORS[tile ?? '#'] ?? 'white', dim: dist > 8};
		for (let y = top; y <= bottom; y++) grid[y]![x] = cell;
	}

	// Sprites: far to near, clipped against the wall depth of each column.
	const invDet = 1 / (planeX * cam.dirY - cam.dirX * planeY);
	const placed = sprites
		.map(s => {
			const sx = s.x - cam.x;
			const sy = s.y - cam.y;
			return {s, tx: invDet * (cam.dirY * sx - cam.dirX * sy), depth: invDet * (-planeY * sx + planeX * sy)};
		})
		.filter(p => p.depth > 0.2)
		.sort((a, b) => b.depth - a.depth);

	for (const {s, tx, depth} of placed) {
		const screenX = (W / 2) * (1 + tx / depth);
		const floorRow = horizon + (0.5 * scale) / depth;
		const rows = (s.height * scale) / depth;
		const put = (px: number, py: number, char: string) => {
			if (px < 0 || px >= W || py < 0 || py >= H || depth >= zBuffer[px]!) return;
			grid[py]![px] = {char, color: s.color, dim: depth > 8};
		};

		const lines = s.art.split('\n');
		const artH = lines.length;
		const artW = Math.max(...lines.map(l => l.length));
		const artScale = Math.min(MAX_ART_SCALE, rows / artH);

		if (artScale < 0.75 || artW === 0) {
			put(Math.floor(screenX), Math.round(floorRow - Math.max(1, rows) / 2), s.glyph);
			continue;
		}
		const outH = Math.round(artH * artScale);
		const outW = Math.round(artW * artScale);
		const left = Math.round(screenX - outW / 2);
		const topRow = Math.round(floorRow - outH);
		for (let oy = 0; oy < outH; oy++) {
			const line = lines[Math.floor(oy / artScale)] ?? '';
			// Spaces outside the drawing are transparent, spaces inside it are solid.
			const first = line.search(/\S/);
			const last = line.trimEnd().length - 1;
			for (let ox = 0; ox < outW; ox++) {
				const i = Math.floor(ox / artScale);
				if (first !== -1 && i >= first && i <= last) put(left + ox, topRow + oy, line[i]!);
			}
		}
	}

	return grid;
}

function shadeIndex(dist: number): number {
	if (dist < 2) return 0;
	if (dist < 4) return 1;
	if (dist < 7) return 2;
	return 3;
}

function floorCell(tile: string | undefined, fx: number, fy: number, dist: number): Cell {
	if (tile === '~') return {char: dist < 3 ? '≈' : '~', color: 'blue', dim: dist > 6};
	if (dist > 7) return {char: '.', dim: true};
	// Checkerboard by tile gives a sense of depth.
	const even = (Math.floor(fx) + Math.floor(fy)) % 2 === 0;
	return even ? {char: dist < 2.5 ? ':' : '·', color: 'gray'} : {char: ' '};
}
