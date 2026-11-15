import { cp, mkdir, readdir, rm, copyFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const target = path.resolve(root, 'sites/escoop/dist');
if (path.relative(root, target) !== path.join('sites', 'escoop', 'dist')) throw new Error('Unexpected output directory');
// Only replace the verified, generated deployment directory; preserve Site identity and Git history.
await readdir(path.join(root, 'dist'));
await rm(target, { recursive: true, force: true });
await mkdir(target, { recursive: true });
await cp(path.join(root, 'dist'), target, { recursive: true });
const checkout = path.dirname(target);
for (const directory of ['src', 'data', 'images', 'scripts', 'tests']) {
  await cp(path.join(root, directory), path.join(checkout, directory), { recursive: true, filter: source => !source.includes('__pycache__') });
}
for (const file of ['index.html', 'package.json', 'package-lock.json', 'tsconfig.json', 'vite.config.ts', 'README.md']) {
  await copyFile(path.join(root, file), path.join(checkout, file));
}
await writeFile(path.join(checkout, '.gitignore'), 'node_modules/\n.tools/\n__pycache__/\nsites/\n');
console.log(`Static site ready: ${target}`);
