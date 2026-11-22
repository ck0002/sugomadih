import type {FC} from 'react';
import type {Action, GameState} from '../types.js';

export type TabProps = {
	state: GameState;
	isActive: boolean; // true when this tab is showing and should take input
	dispatch: (action: Action) => void; // send what the player did
};

// One tab in the bottom menu. To add a tab: make a file in ./tabs and add it to ./tabs/index.ts.
export type MenuTab = {
	id: string;
	label: string;
	Component: FC<TabProps>;
	visible?: (state: GameState) => boolean; // hide the tab unless this returns true (e.g. debug only)
};
