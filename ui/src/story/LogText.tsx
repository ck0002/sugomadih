import {Box, Text} from 'ink';

type Props = {log: string[]; fresh: number; lines: number};

// Last few log lines; the ones the last action added are bright, older ones dim.
export function LogText({log, fresh, lines}: Props) {
	const shown = log.slice(-lines);
	const firstFresh = shown.length - Math.min(fresh, shown.length);
	return (
		<Box flexDirection="column">
			{shown.map((line, i) => (
				<Text key={log.length - shown.length + i} wrap="truncate" dimColor={i < firstFresh} color={colorFor(line)}>
					{line}
				</Text>
			))}
		</Box>
	);
}

function colorFor(line: string): string | undefined {
	if (line.startsWith('—')) return 'cyan'; // room header
	if (/^You (hit|drink|ready)/.test(line)) return 'green';
	if (/hits you|You fall|You have fallen|you are/i.test(line)) return 'red';
	return undefined;
}
