import type {MenuTab} from '../types.js';
import {debugTab} from './DebugTab.js';
import {fightTab} from './FightTab.js';
import {itemsTab} from './ItemsTab.js';
import {optionsTab} from './OptionsTab.js';
import {partyTab} from './PartyTab.js';
import {settingsTab} from './SettingsTab.js';
import {storyTab} from './StoryTab.js';

// The bottom menu shows these tabs in this order. Add a new tab here.
export const TABS: MenuTab[] = [fightTab, itemsTab, partyTab, storyTab, settingsTab, optionsTab, debugTab];
