// Runs the Python engine (engine/server.py) as a child process and talks JSON lines over stdio.
// Engine logs (stderr) go to engine.log in the repo root, so they never draw over the UI.
import {spawn, type ChildProcess} from 'node:child_process';
import {openSync} from 'node:fs';
import {join} from 'node:path';
import {createInterface} from 'node:readline';
import {fileURLToPath} from 'node:url';
import {useCallback, useEffect, useRef, useState} from 'react';
import type {Action, GameState} from '../types.js';

// Messages from the engine. Keep in sync with engine/server.py.
type EngineMessage =
	| {type: 'loading'; message: string}
	| {type: 'state'; state: GameState; narration: string; message: string}
	| {type: 'error'; message: string};

const REPO_ROOT = fileURLToPath(new URL('../../..', import.meta.url));

export type Engine = {
	state: GameState | null;
	narration: string; // the LLM's story text for the current room
	message: string; // feedback for the last action
	loading: string | null; // set while the engine (LLM) is working
	dispatch: (action: Action) => void;
};

export function useEngine(): Engine {
	const [state, setState] = useState<GameState | null>(null);
	const [narration, setNarration] = useState('');
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
				case 'state':
					setState(msg.state);
					setNarration(msg.narration);
					setMessage(msg.message);
					setLoading(null);
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

	return {state, narration, message, loading, dispatch};
}
