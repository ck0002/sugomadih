import {useState} from 'react';
import {Box, Text} from 'ink';
import {DamageText, Effectiveness, StatusList} from '../../combat/DamageText.js';
import {HpBar} from '../../components/HpBar.js';
import {SelectList} from '../../components/SelectList.js';
import {entityAt, tileAhead} from '../../state.js';
import type {MenuTab, TabProps} from '../types.js';

// Pick an attack (weapon or spell) and use it on whatever stands in front of you.
function FightTab({state, isActive, dispatch}: TabProps) {
	const player = state.party[0]!;
	const attacks = player.available_attacks;
	const [index, setIndex] = useState(0);
	const attack = attacks[index];
	const ahead = tileAhead(state);
	const target = entityAt(state, ahead.x, ahead.y);
	const enemy = target?.kind === 'character' && target.hostile ? target : undefined;

	return (
		<Box columnGap={3}>
			<Box width={22} flexDirection="column">
				<SelectList
					entries={attacks.map((a, i) => ({key: `${a.name}-${i}`, label: a.name}))}
					isActive={isActive}
					onHighlight={setIndex}
					onSelect={i => dispatch({type: 'attack', attack: i})}
				/>
			</Box>
			{attack && (
				<Box flexDirection="column" width={44} flexShrink={1}>
					<Text bold>{attack.name}</Text>
					<DamageText attack={attack} types={state.damage_types} />
					{attack.damage.map((roll, i) => {
						const info = state.damage_types[roll.type];
						return info ? (
							<Text key={i} dimColor wrap="wrap">
								{info.lineage.slice(0, -1).reverse().join(' › ')}: {info.description}
							</Text>
						) : null;
					})}
				</Box>
			)}
			<Box flexDirection="column" flexShrink={1}>
				{enemy ? (
					<>
						<Text bold color="red">
							{enemy.name} <Text dimColor>AC {enemy.armor_class}</Text>
						</Text>
						<HpBar hp={enemy.hp} max={enemy.total_stats.max_hp} />
						<StatusList target={enemy} />
						{attack && <Effectiveness attack={attack} target={enemy} types={state.damage_types} />}
					</>
				) : (
					<Text dimColor>No enemy ahead. Face one and press enter (or f).</Text>
				)}
			</Box>
		</Box>
	);
}

export const fightTab: MenuTab = {id: 'fight', label: 'FIGHT', Component: FightTab};
