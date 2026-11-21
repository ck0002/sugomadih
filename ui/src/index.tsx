import {render, useApp} from 'ink';
import {App} from './App.js';
import {usePress} from './input/keys.js';
import {AnimationClock} from './render/animation.js';
import {SettingsProvider} from './settings/settings.js';

function Root() {
	const {exit} = useApp();
	usePress(input => {
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

// kitty keyboard protocol (where the terminal supports it) gives key release events,
// which makes held movement keys precise. Other terminals fall back automatically (input/holdRepeat.ts).
render(<Root />, {
	alternateScreen: true,
	kittyKeyboard: {
		mode: 'auto',
		// All keys as escape codes so letter presses carry an event type too (otherwise only releases would).
		flags: ['disambiguateEscapeCodes', 'reportEventTypes', 'reportAllKeysAsEscapeCodes', 'reportAssociatedText'],
	},
});
