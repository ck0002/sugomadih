import type {MenuTab} from '../types.js';
import {itemsTab} from './ItemsTab.js';
import {optionsTab} from './OptionsTab.js';
import {partyTab} from './PartyTab.js';

// The bottom menu shows these tabs in this order. Add a new tab here.
export const TABS: MenuTab[] = [itemsTab, partyTab, optionsTab];
