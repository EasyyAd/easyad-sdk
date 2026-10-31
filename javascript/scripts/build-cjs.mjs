// Génère dist/index.cjs (pour require()) à partir de src/index.js (ESM). Lancé automatiquement avant chaque publication.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';

const src = readFileSync(new URL('../src/index.js', import.meta.url), 'utf8');
const cjs = `'use strict';\n${src
  .replace(/^export class /gm, 'class ')
  .replace(/^export default EasyAd;\s*$/m, '')}
module.exports = EasyAd;
module.exports.EasyAd = EasyAd;
module.exports.EasyAdError = EasyAdError;
module.exports.default = EasyAd;
`;
if (/^\s*(export|import)\s/m.test(cjs)) throw new Error('Syntaxe ESM restante dans la version CommonJS');
mkdirSync(new URL('../dist/', import.meta.url), { recursive: true });
writeFileSync(new URL('../dist/index.cjs', import.meta.url), cjs);
console.log('dist/index.cjs généré');
