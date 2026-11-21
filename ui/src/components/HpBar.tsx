import {Text} from 'ink';

type Props = {hp: number; max: number; width?: number};

export function HpBar({hp, max, width = 10}: Props) {
	const filled = max > 0 ? Math.min(width, Math.round((Math.max(0, hp) / max) * width)) : 0;
	const color = hp / max > 0.5 ? 'green' : hp / max > 0.25 ? 'yellow' : 'red';
	return (
		<Text>
			<Text color={color}>{'█'.repeat(filled)}</Text>
			<Text dimColor>{'░'.repeat(width - filled)}</Text> {hp}/{max}
		</Text>
	);
}
