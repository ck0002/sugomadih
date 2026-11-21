import {useState} from 'react';
import {Box, Text} from 'ink';
import {StatusList} from '../../combat/DamageText.js';
import {HpBar} from '../../components/HpBar.js';
import {AnimatedArt} from '../../components/AnimatedArt.js';
import {SelectList} from '../../components/SelectList.js';
import {StatBlock} from '../../components/StatBlock.js';
import type {MenuTab, TabProps} from '../types.js';

function PartyTab({state, isActive, dispatch}: TabProps) {
	const {party} = state;
	const [index, setIndex] = useState(0);
	const member = party[index];

	return (
		<Box columnGap={3}>
			<Box width={22} flexDirection="column">
				<SelectList
					entries={party.map(c => ({key: c.id, label: c.name}))}
					isActive={isActive}
					onHighlight={setIndex}
					onSelect={i => dispatch({type: 'inspect', entityId: party[i]!.id})}
				/>
			</Box>
			{member && (
				<>
					<AnimatedArt entity={member} color="green" />
					<Box flexDirection="column" flexShrink={1}>
						<Text bold>{member.name}</Text>
						<Text dimColor>{member.description}</Text>
						<Text>
							<HpBar hp={member.hp} max={member.total_stats.max_hp} />
							<Text dimColor>   AC </Text>
							{member.armor_class}
						</Text>
						<StatusList target={member} />
						<StatBlock stats={member.total_stats} />
					</Box>
				</>
			)}
		</Box>
	);
}

export const partyTab: MenuTab = {id: 'party', label: 'PARTY', Component: PartyTab};
