import type {MenuTab} from '../types.js';
import {fightTab} from './FightTab.js';
import {itemsTab} from './ItemsTab.js';
import {optionsTab} from './OptionsTab.js';
import {partyTab} from './PartyTab.js';
import {settingsTab} from './SettingsTab.js';

// The bottom menu shows these tabs in this order. Add a new tab here.
export const TABS: MenuTab[] = [fightTab, itemsTab, partyTab, settingsTab, optionsTab];
