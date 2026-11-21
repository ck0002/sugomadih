import {Box, Text} from 'ink';

// One character on screen with its style. Map, minimap and 3D view all render grids of these.
export type Cell = {char: string; color?: string; dim?: boolean};

type Props = {grid: Cell[][]};

export function CellGrid({grid}: Props) {
	return (
		<Box flexDirection="column">
			{grid.map((row, y) => (
				<Text key={y} wrap="truncate">
					{groupRuns(row).map((run, i) => (
						<Text key={i} color={run.color} dimColor={run.dim}>
							{run.char}
						</Text>
					))}
				</Text>
			))}
		</Box>
	);
}

// Merge neighbouring cells with the same style so we render a few <Text>s per row, not one per cell.
function groupRuns(row: Cell[]): Cell[] {
	const runs: Cell[] = [];
	for (const c of row) {
		const last = runs.at(-1);
		if (last && last.color === c.color && last.dim === c.dim) last.char += c.char;
		else runs.push({...c});
	}
	return runs;
}
