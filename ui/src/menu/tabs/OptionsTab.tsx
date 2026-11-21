import {useApp} from 'ink';
import {SelectList} from '../../components/SelectList.js';
import type {MenuTab, TabProps} from '../types.js';

const OPTIONS = ['Save', 'Load', 'Quit'];

function OptionsTab({isActive, dispatch}: TabProps) {
	const {exit} = useApp();
	return (
		<SelectList
			entries={OPTIONS.map(o => ({key: o, label: o}))}
			isActive={isActive}
			onSelect={i => (OPTIONS[i] === 'Quit' ? exit() : dispatch({type: 'option', option: OPTIONS[i]!}))}
		/>
	);
}

export const optionsTab: MenuTab = {id: 'options', label: 'OPTIONS', Component: OptionsTab};
