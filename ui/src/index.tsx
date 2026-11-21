import {render, useApp, useInput} from 'ink';
import {App} from './App.js';
import {AnimationClock} from './render/animation.js';
import {SettingsProvider} from './settings/settings.js';

function Root() {
	const {exit} = useApp();
	useInput(input => {
		if (input === 'q') exit();
	});
	return (
		<SettingsProvider>
			<AnimationClock>
				<App />
			</AnimationClock>
		</SettingsProvider>
	);
}

render(<Root />, {alternateScreen: true});
