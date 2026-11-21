import {render, useApp, useInput} from 'ink';
import {App} from './App.js';

function Root() {
	const {exit} = useApp();
	useInput(input => {
		if (input === 'q') exit();
	});
	return <App />;
}

render(<Root />, {alternateScreen: true});
