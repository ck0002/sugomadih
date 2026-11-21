// Fake game state so the UI runs before the Python bridge exists.
import type {Character, GameState, Item, Stats} from '../types.js';
import {SPRITES} from './sprites.js';

const stats = (s: Partial<Stats>): Stats => ({
	strength: 0,
	dexterity: 0,
	constitution: 0,
	intelligence: 0,
	wisdom: 0,
	charisma: 0,
	max_hp: 0,
	...s,
});

const sword: Item = {
	kind: 'item',
	id: 'sword01',
	name: 'Rusty Sword',
	description: 'Seen better days, still pointy.',
	art: SPRITES.sword,
	animation: 'idle',
	stats: stats({strength: 2}),
	value: 5,
};

const potion: Item = {
	kind: 'item',
	id: 'potion01',
	name: 'Red Potion',
	description: 'Smells like cherries and regret.',
	art: SPRITES.potion,
	animation: 'idle',
	stats: stats({max_hp: 5}),
	value: 10,
};

const amulet: Item = {
	kind: 'item',
	id: 'amulet01',
	name: 'Owl Amulet',
	description: 'The owl watches. The owl knows.',
	art: SPRITES.amulet,
	animation: 'idle',
	stats: stats({wisdom: 1, charisma: 1}),
	value: 25,
};

const player: Character = {
	kind: 'character',
	id: 'player',
	name: 'You',
	description: 'A hopeful adventurer.',
	art: SPRITES.player,
	animation: 'idle',
	stats: stats({strength: 12, dexterity: 14, constitution: 12, intelligence: 10, wisdom: 11, charisma: 13, max_hp: 20}),
	hostile: false,
	dialogue: [],
	inventory: [sword, potion, amulet],
	hp: 17,
};

const brena: Character = {
	kind: 'character',
	id: 'brena',
	name: 'Brena',
	description: 'Dwarf cleric. Hums when nervous.',
	art: SPRITES.brena,
	animation: 'idle',
	stats: stats({strength: 14, dexterity: 8, constitution: 15, intelligence: 10, wisdom: 15, charisma: 9, max_hp: 24}),
	hostile: false,
	dialogue: ['Stay behind me, lad.'],
	inventory: [],
	hp: 24,
};

const goblin: Character = {
	kind: 'character',
	id: 'goblin01',
	name: 'Goblin',
	description: 'Small, green, very interested in your pockets.',
	art: SPRITES.goblin,
	animation: 'idle',
	stats: stats({strength: 8, dexterity: 14, max_hp: 7}),
	hostile: true,
	dialogue: ['Shiny! Give!'],
	inventory: [],
	hp: 7,
};

const merchant: Character = {
	kind: 'character',
	id: 'merchant01',
	name: 'Old Merchant',
	description: 'Sells things. Mostly junk.',
	art: SPRITES.merchant,
	animation: 'idle',
	stats: stats({charisma: 14, max_hp: 6}),
	hostile: false,
	dialogue: ['Wares! Fine wares!'],
	inventory: [],
	hp: 6,
};

const chestKey: Item = {
	kind: 'item',
	id: 'key01',
	name: 'Brass Key',
	description: 'Opens something, somewhere.',
	art: SPRITES.key,
	animation: 'idle',
	stats: stats({}),
	value: 1,
};

export const mockState: GameState = {
	party: [player, brena],
	entities: Object.fromEntries([player, brena, goblin, merchant, chestKey].map(e => [e.id, e])),
	map: {
		name: 'Cellar of the Leaky Tankard',
		tiles: [
			'##########################################',
			'#........#...............................#',
			'#........#.......~~~~....................#',
			'#........+.......~~~~~~..........#####...#',
			'#........#........~~~~...........#...#...#',
			'######+###.......................#...+...#',
			'#........................................#',
			'#..........####.........................##',
			'#..........#..#..........................+',
			'#..........####..........................#',
			'#........................................#',
			'##########################################',
		],
		placements: [
			// Party members (Brena) travel with the player, so only the player is placed.
			{id: 'player', x: 12, y: 6, facing: 'E'},
			{id: 'goblin01', x: 26, y: 8},
			{id: 'merchant01', x: 36, y: 4},
			{id: 'key01', x: 13, y: 8},
		],
	},
};
