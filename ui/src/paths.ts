import {fileURLToPath} from 'node:url';

// Repo root (ui/src/paths.ts -> ../../). The engine runs from here; settings and engine.log live here.
export const REPO_ROOT = fileURLToPath(new URL('../../', import.meta.url));
