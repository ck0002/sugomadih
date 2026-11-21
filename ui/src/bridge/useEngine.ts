// Runs the Python engine (engine/server.py) as a child process and talks JSON lines over stdio.
// Engine logs (stderr) go to engine.log in the repo root, so they never draw over the UI.
import {spawn, type ChildProcess} from 'node:child_process';
import {openSync} from 'node:fs';
import {join} from 'node:path';
import {createInterface} from 'node:readline';
import {useCallback, useEffect, useRef, useState} from 'react';
import {REPO_ROOT} from '../paths.js';
import type {Action, GameState} from '../types.js';

// Messages from the engine. Keep in sync with engine/server.py.
type EngineMessage =
	| {type: 'loading'; message: string}
	| {type: 'state'; state: GameState; narration: string; message: string}
	| {type: 'narrating'}
	| {type: 'narration'; text: string}
	| {type: 'error'; message: string};

export type Engine = {
	state: GameState | null;
	narration: string; // the game master's latest words (room intro, then combat retellings)
	narrating: boolean; // the LLM is writing a combat retelling
	message: string; // feedback for the last action
	loading: string | null; // set while the engine (LLM) is working
	dispatch: (action: Action) => void;
};

export function useEngine(): Engine {
	const [state, setState] = useState<GameState | null>(null);
	const [narration, setNarration] = useState('');
	const [narrating, setNarrating] = useState(false);
	const roomKey = useRef('');
	const [message, setMessage] = useState('');
	const [loading, setLoading] = useState<string | null>('Starting the engine...');
	const proc = useRef<ChildProcess | null>(null);

	useEffect(() => {
		const log = openSync(join(REPO_ROOT, 'engine.log'), 'a');
		const child = spawn('uv', ['run', '--quiet', 'python', '-m', 'engine.server'], {
			cwd: REPO_ROOT,
			stdio: ['pipe', 'pipe', log],
		});
		proc.current = child;

		createInterface({input: child.stdout!}).on('line', line => {
			let msg: EngineMessage;
			try {
				msg = JSON.parse(line) as EngineMessage;
			} catch {
				return; // not a protocol line
			}
			switch (msg.type) {
				case 'loading':
					setLoading(msg.message);
					break;
				case 'state': {
					// Narration from a state message only counts for a new room; during play the
					// newer 'narration' messages win (a state can carry an older retelling).
					const key = `${msg.state.run}:${msg.state.room}`;
					if (key !== roomKey.current) {
						roomKey.current = key;
						setNarration(msg.narration);
						setNarrating(false);
					}
					setState(msg.state);
					setMessage(msg.message);
					setLoading(null);
					break;
				}
				case 'narrating':
					setNarrating(true);
					break;
				case 'narration':
					setNarration(msg.text);
					setNarrating(false);
					break;
				case 'error':
					setMessage(`Engine error: ${msg.message}`);
					setLoading(null);
					break;
			}
		});
		child.on('error', err => {
			setLoading(null);
			setMessage(`Could not start the engine: ${err.message}`);
		});
		child.on('exit', code => {
			setLoading(null);
			setMessage(`Engine stopped (code ${code}). See engine.log.`);
		});

		const kill = () => child.kill();
		process.on('exit', kill);
		return () => {
			process.off('exit', kill);
			kill();
		};
	}, []);

	const dispatch = useCallback((action: Action) => {
		proc.current?.stdin?.write(JSON.stringify({type: 'action', action}) + '\n');
	}, []);

	return {state, narration, narrating, message, loading, dispatch};
}
