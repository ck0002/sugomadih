// Mirrors the Python models in engine/models (the shape of Entity.to_dict()).

export type Stats = {
	strength: number;
	dexterity: number;
	constitution: number;
	intelligence: number;
	wisdom: number;
	charisma: number;
	max_hp: number;
};

type EntityBase = {
	id: string;
	name: string;
	description: string;
	art: string;
	stats: Stats;
};

export type Item = EntityBase & {
	kind: 'item';
	value: number;
};

export type Character = EntityBase & {
	kind: 'character';
	hostile: boolean;
	dialogue: string[];
	inventory: Item[];
	hp: number;
};

export type Entity = Item | Character;

export type Direction = 'N' | 'E' | 'S' | 'W';

export type Placement = {id: string; x: number; y: number; facing?: Direction};

export type MapState = {
	name: string;
	tiles: string[]; // one string per row
	placements: Placement[]; // where entities stand on the map
};

export type GameState = {
	party: Character[]; // party[0] is the player
	entities: Record<string, Entity>; // everything on the map, by id
	map: MapState;
};

// What the UI sends back when the player does something.
// Later this goes to the Python engine; for now App just shows it.
export type Action =
	| {type: 'move'; dir: 'forward' | 'back'}
	| {type: 'turn'; dir: 'left' | 'right'}
	| {type: 'use_item'; itemId: string}
	| {type: 'inspect'; entityId: string}
	| {type: 'option'; option: string};
