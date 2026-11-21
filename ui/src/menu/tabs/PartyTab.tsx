import {useState} from 'react';
import {Box, Text} from 'ink';
import {HpBar} from '../../components/HpBar.js';
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
					<Text color="green">{member.art}</Text>
					<Box flexDirection="column" flexShrink={1}>
						<Text bold>{member.name}</Text>
						<Text dimColor>{member.description}</Text>
						<HpBar hp={member.hp} max={member.stats.max_hp} />
						<StatBlock stats={member.stats} />
					</Box>
				</>
			)}
		</Box>
	);
}

export const partyTab: MenuTab = {id: 'party', label: 'PARTY', Component: PartyTab};
