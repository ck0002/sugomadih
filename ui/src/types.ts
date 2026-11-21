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

// Animation name -> frames. Each frame is a multi-line ASCII string.
// Every entity has "idle"; others ("attack", "hurt", ...) are optional.
export type Animations = Record<string, string[]>;

type EntityBase = {
	id: string;
	name: string;
	description: string;
	art: Animations;
	animation: string; // which animation is playing now
	stats: Stats;
};

// ---- combat (engine/combat) ----

export type DamageRoll = {dice: string; type: string}; // type = damage type id ("sharp", "fire", ...)

export type Attack = {
	name: string;
	damage: DamageRoll[]; // several rolls = mixed damage
	stat: keyof Stats; // adds to hit and damage
};

export type StatusEffect = {
	id: string;
	name: string;
	turns: number;
	damage_per_turn: number;
	damage_type: string | null;
	skip_turn: boolean;
	ac_penalty: number;
};

// Sent by Python (damage_type_info()), so the UI never hardcodes damage types.
export type DamageTypeInfo = {
	name: string;
	category: string; // "physical" | "magic"
	color: string;
	description: string;
	lineage: string[]; // ["dull", "physical", "damage"]
};

// ---- entities ----

type ItemBase = EntityBase & {value: number};

export type PlainItem = ItemBase & {kind: 'item'};
export type Weapon = ItemBase & {kind: 'weapon'; attack: Attack};
export type Potion = ItemBase & {kind: 'potion'; heal: number};
export type Item = PlainItem | Weapon | Potion;

export type Character = EntityBase & {
	kind: 'character';
	hostile: boolean;
	dialogue: string[];
	inventory: Item[];
	hp: number;
	attacks: Attack[]; // natural attacks / spells
	resistances: Record<string, number>; // by damage type or category id; 0 immune, 0.5 resists, 2 weak
	damage_multipliers: Record<string, number>; // final multiplier per damage type id (computed by Python)
	statuses: StatusEffect[];
	// computed by Python:
	total_stats: Stats; // stats + buffs from carried items
	armor_class: number;
	available_attacks: Attack[]; // weapons first (index 0 = default attack), then attacks
};

export type Entity = Item | Character;

export const isItem = (e: Entity): e is Item => e.kind !== 'character';

export type Direction = 'N' | 'E' | 'S' | 'W';

export type Placement = {id: string; x: number; y: number; facing?: Direction};

export type MapState = {
	name: string;
	theme: string; // look of the room, see view3d/themes.ts
	tiles: string[]; // one string per row
	placements: Placement[]; // where entities stand on the map
};

export type GameState = {
	room: number; // how many rooms deep we are
	run: number; // which attempt (goes up when the party dies and a new run starts)
	party: Character[]; // party[0] is the player
	entities: Record<string, Entity>; // everything on the map, by id
	map: MapState;
	log: string[]; // combat / event log, newest last
	log_fresh: number; // how many of the last log lines came from the last action
	damage_types: Record<string, DamageTypeInfo>;
};

// What the UI sends to the Python engine when the player does something (engine/game.py handle()).
export type Action =
	| {type: 'move'; dir: 'forward' | 'back'}
	| {type: 'turn'; dir: 'left' | 'right'}
	| {type: 'attack'; attack: number} // index into the player's available_attacks, at the tile ahead
	| {type: 'use_item'; itemId: string}
	| {type: 'inspect'; entityId: string}
	| {type: 'option'; option: string};
