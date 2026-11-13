/** Synchronize original symbol and favicon exports from the GitHub branding branch.
 * Full wordmarks now ship locally from the user's two provided images under
 * public/branding/custom/; do not overwrite them from the older GitHub exports.
 * Verify Git blob SHA-1 for every remaining remote asset. */
import { createHash } from 'node:crypto';
import { mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const destination = join(repoRoot, 'public', 'branding', 'official');
const base = 'https://raw.githubusercontent.com/Proyecto-Software-I/frontend/feat/29-branding/public/branding/';
const assets = [
  [
    "symbol-dark/webp/symbol-dark-128.webp",
    "symbol-dark.webp",
    "ac98a04758e3424b13b21a845e095a7751af5d3f"
  ],
  [
    "symbol-light/webp/symbol-light-128.webp",
    "symbol-light.webp",
    "f2c6758dc75c7d051201741a830445edca8e7c91"
  ],
  [
    "favicon/favicon-dark-32x32.png",
    "favicon-dark-32x32.png",
    "eae16fb40dfc685b2b1c96a657e8bf85bb84a12f"
  ],
  [
    "favicon/favicon-light-32x32.png",
    "favicon-light-32x32.png",
    "02c8c8cc0ef68bdc9a5af19dda1ebee76e5a5c68"
  ],
  [
    "favicon/favicon.ico",
    "favicon.ico",
    "8d156890d478043325fba4aebff9f4f4ae2b61dd"
  ],
  [
    "favicon/apple-touch-icon.png",
    "apple-touch-icon.png",
    "23aaa25280b9b84f7af7436c78aad0eff0759a97"
  ],
  [
    "favicon/android-chrome-192x192.png",
    "android-chrome-192x192.png",
    "767d7ebb665765290864eb1ee91d7bcea3501eeb"
  ],
  [
    "favicon/android-chrome-512x512.png",
    "android-chrome-512x512.png",
    "b87c0c390d75d61c043b2177da3d41353dbed8a3"
  ]
];

const hashBlob = bytes => createHash('sha1').update(`blob ${bytes.length}\0`).update(bytes).digest('hex');
async function main() {
  await mkdir(destination, { recursive: true });
  for (const [source, name, expected] of assets) {
    const target = join(destination, name);
    try { if (hashBlob(await readFile(target)) === expected) { console.log(`OK  ${name} (cache)`); continue; } } catch { /* missing */ }
    const response = await fetch(base + source, { signal: AbortSignal.timeout(20000) });
    if (!response.ok) throw new Error(`Github HTTP ${response.status} for ${source}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    if (hashBlob(bytes) !== expected) throw new Error(`La imagen ${name} ha cambiado respecto a la versión aprobada. Revisa el branding antes de actualizar.`);
    const tmp = `${target}.tmp`;
    try { await writeFile(tmp, bytes); await rename(tmp, target); }
    finally { await rm(tmp, { force: true }); }
    console.log(`OK  ${name} (${bytes.length} bytes)`);
  }
  console.log('Branding oficial sincronizado y verificado.');
}
main().catch(error => { console.error('No se pudieron sincronizar los logos oficiales:',error.message); process.exitCode = 1; });
