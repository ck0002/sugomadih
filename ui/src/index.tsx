import {render, useApp, useInput} from 'ink';
import {App} from './App.js';
import {AnimationClock} from './render/animation.js';

function Root() {
	const {exit} = useApp();
	useInput(input => {
		if (input === 'q') exit();
	});
	return (
		<AnimationClock>
			<App />
		</AnimationClock>
	);
}

render(<Root />, {alternateScreen: true});
