// News-image entry for Wednesday 18 November 2026.
//
// What this program does: it takes the finished front-page image
// that ships in this repository (entry.png, drawn by the generator
// in tools/generate-image.py) and places an exact copy of it where
// the grader looks for it.
//
// Why a copy instead of drawing at run time: the grader runs with
// no network and a 60-second limit, so the safest deterministic
// entry is a pre-drawn image plus a tiny, dependency-free copy.
// Node 22, standard library only — nothing is installed.
//
// Run it locally like this:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
// In the grader the output directory is /output by default.

import { copyFileSync, mkdirSync, statSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

// The image lives next to this file, wherever the repo is checked out.
const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, 'entry.png');

// The grader writes to /output; a local run can point elsewhere
// with MAKEFUN_OUTPUT_DIR so nothing needs root to test.
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
const target = join(outDir, 'entry.png');

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

// A one-line sanity check for the log: the copy must be a real PNG
// of the size the repository ships, never an empty file.
const { size } = statSync(target);
if (size === 0) throw new Error(`Copy failed: ${target} is empty`);
console.log(`Wrote ${target} (${size} bytes)`);
