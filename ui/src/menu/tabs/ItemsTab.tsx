import {useState} from 'react';
import {Box, Text} from 'ink';
import {SelectList} from '../../components/SelectList.js';
import {StatBlock} from '../../components/StatBlock.js';
import type {MenuTab, TabProps} from '../types.js';

function ItemsTab({state, isActive, dispatch}: TabProps) {
	const items = state.party[0]?.inventory ?? [];
	const [index, setIndex] = useState(0);
	const item = items[index];

	return (
		<Box columnGap={3}>
			<Box width={22} flexDirection="column">
				<SelectList
					entries={items.map(i => ({key: i.id, label: i.name}))}
					isActive={isActive}
					onHighlight={setIndex}
					onSelect={i => dispatch({type: 'use_item', itemId: items[i]!.id})}
				/>
			</Box>
			{item && (
				<>
					<Text color="cyan">{item.art}</Text>
					<Box flexDirection="column" flexShrink={1}>
						<Text bold>{item.name}</Text>
						<Text dimColor>{item.description}</Text>
						<StatBlock stats={item.stats} buffs />
						<Text color="yellow">{item.value}g</Text>
					</Box>
				</>
			)}
		</Box>
	);
}

export const itemsTab: MenuTab = {id: 'items', label: 'ITEMS', Component: ItemsTab};
