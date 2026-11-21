import {useState} from 'react';
import {Box, Text} from 'ink';
import {DamageText} from '../../combat/DamageText.js';
import {AnimatedArt} from '../../components/AnimatedArt.js';
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
					<AnimatedArt entity={item} color="cyan" />
					<Box flexDirection="column" flexShrink={1}>
						<Text bold>{item.name}</Text>
						<Text dimColor>{item.description}</Text>
						{item.kind === 'weapon' && <DamageText attack={item.attack} types={state.damage_types} />}
						{item.kind === 'potion' && <Text color="green">Heals {item.heal} hp</Text>}
						<StatBlock stats={item.stats} buffs />
						<Text>
							<Text color="yellow">{item.value}g</Text>
							<Text dimColor>
								{item.kind === 'weapon' ? '   enter: ready (default attack)' : item.kind === 'potion' ? '   enter: drink' : ''}
							</Text>
						</Text>
					</Box>
				</>
			)}
		</Box>
	);
}

export const itemsTab: MenuTab = {id: 'items', label: 'ITEMS', Component: ItemsTab};
