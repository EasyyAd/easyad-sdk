import test from 'node:test';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);

test('le paquet se charge aussi avec require() (Telegraf, projets CommonJS)', () => {
  const EasyAd = require('../dist/index.cjs');
  assert.equal(typeof EasyAd, 'function');
  assert.equal(EasyAd.EasyAd, EasyAd);
  assert.equal(typeof EasyAd.EasyAdError, 'function');
  const client = new EasyAd({ apiKey: 'ea_test_x' });
  assert.equal(typeof client.nextAd, 'function');
});

test('les exports déclarés existent', async () => {
  const pkg = require('../package.json');
  const fs = await import('node:fs');
  for (const f of [pkg.exports['.'].import, pkg.exports['.'].require, pkg.exports['.'].types]) {
    assert.ok(fs.existsSync(new URL(`../${f}`, import.meta.url)), f);
  }
});
