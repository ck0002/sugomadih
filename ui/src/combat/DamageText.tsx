import {Text} from 'ink';
import type {Attack, Character, DamageTypeInfo} from '../types.js';

type Types = Record<string, DamageTypeInfo>;

const STAT_SHORT: Record<string, string> = {
	strength: 'STR',
	dexterity: 'DEX',
	constitution: 'CON',
	intelligence: 'INT',
	wisdom: 'WIS',
	charisma: 'CHA',
};

// "1d6 sharp + 1d4 fire (STR)", each part in its damage type's colour.
export function DamageText({attack, types}: {attack: Attack; types: Types}) {
	return (
		<Text>
			{attack.damage.map((roll, i) => (
				<Text key={i}>
					{i > 0 && ' + '}
					<Text color={types[roll.type]?.color}>
						{roll.dice} {types[roll.type]?.name.toLowerCase() ?? roll.type}
					</Text>
				</Text>
			))}
			<Text dimColor> ({STAT_SHORT[attack.stat] ?? attack.stat})</Text>
		</Text>
	);
}

// How well each part of `attack` works on `target`: "fire ×2 weak", "sharp ×0.5 resists".
export function Effectiveness({attack, target, types}: {attack: Attack; target: Character; types: Types}) {
	return (
		<Text>
			{attack.damage.map((roll, i) => {
				const mult = target.damage_multipliers[roll.type] ?? 1;
				const [label, color] =
					mult === 0 ? ['immune', 'gray'] : mult > 1 ? ['weak', 'green'] : mult < 1 ? ['resists', 'red'] : ['normal', undefined];
				return (
					<Text key={i}>
						{i > 0 && '  '}
						<Text color={types[roll.type]?.color}>{types[roll.type]?.name ?? roll.type}</Text>{' '}
						<Text color={color}>
							×{mult} {label}
						</Text>
					</Text>
				);
			})}
		</Text>
	);
}

export function StatusList({target}: {target: Character}) {
	if (target.statuses.length === 0) return null;
	return (
		<Text color="magenta">{target.statuses.map(s => `${s.name} (${s.turns})`).join(', ')}</Text>
	);
}
