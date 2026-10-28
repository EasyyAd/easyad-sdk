import test from 'node:test';
import assert from 'node:assert/strict';
import { EasyAd, EasyAdError } from '../src/index.js';

/** Remplace fetch le temps d'un test, et renvoie les appels enregistrés. */
function withFetch(responder) {
  const calls = [];
  globalThis.fetch = async (url, init) => {
    calls.push({ url, init, body: init.body ? JSON.parse(init.body) : null });
    const r = await responder({ url, init, call: calls.length });
    return {
      ok: r.status < 400,
      status: r.status,
      text: async () => (r.body === undefined ? '' : JSON.stringify(r.body)),
    };
  };
  return calls;
}

const ADS = {
  ad: {
    placement_id: 'pl_abc1234567',
    text: '<b>Offre</b>\n\nTexte\n\n#Ad #EasyAd',
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[{ text: 'Découvrir', url: 'https://go.easyyad.com/r/xyz' }]] },
    image_url: null,
    label: '#Ad #EasyAd',
    confirm_within_seconds: 1800,
  },
};

test('la clé est obligatoire', () => {
  assert.throws(() => new EasyAd({}), EasyAdError);
});

test('une annonce est renvoyée en forme lisible', async () => {
  withFetch(() => ({ status: 200, body: ADS }));
  const ad = await new EasyAd({ apiKey: 'ea_live_test' }).nextAd({ userId: 42, locale: 'fr' });

  assert.equal(ad.placementId, 'pl_abc1234567');
  assert.equal(ad.parseMode, 'HTML');
  assert.equal(ad.imageUrl, null);
  assert.deepEqual(ad.replyMarkup.inline_keyboard[0][0].text, 'Découvrir');
});

test('l\'identifiant de l\'utilisateur ne quitte jamais le bot en clair', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  await new EasyAd({ apiKey: 'ea_live_test' }).nextAd({ userId: 123456789 });

  const sent = calls[0].body.user_ref;
  assert.equal(sent.length, 32);
  assert.ok(!sent.includes('123456789'));
  assert.match(sent, /^[0-9a-f]{32}$/);
});

test('le même utilisateur donne toujours la même empreinte', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  const sdk = new EasyAd({ apiKey: 'ea_live_test' });
  await sdk.nextAd({ userId: 7 });
  await sdk.nextAd({ userId: 7 });
  assert.equal(calls[0].body.user_ref, calls[1].body.user_ref);
});

test('deux clés différentes ne produisent pas la même empreinte', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  await new EasyAd({ apiKey: 'ea_live_a' }).nextAd({ userId: 7 });
  await new EasyAd({ apiKey: 'ea_live_b' }).nextAd({ userId: 7 });
  assert.notEqual(calls[0].body.user_ref, calls[1].body.user_ref);
});

test('userId est exigé : sans lui, la fréquence ne peut pas être limitée', async () => {
  withFetch(() => ({ status: 200, body: ADS }));
  await assert.rejects(() => new EasyAd({ apiKey: 'k' }).nextAd({}), EasyAdError);
});

test('aucune annonce disponible renvoie null', async () => {
  withFetch(() => ({ status: 200, body: { ad: null, reason: 'no_fill' } }));
  assert.equal(await new EasyAd({ apiKey: 'k' }).nextAd({ userId: 1 }), null);
});

test('un quota atteint renvoie null sans faire de bruit', async () => {
  const seen = [];
  withFetch(() => ({ status: 429, body: { error: 'frequency_capped', message: 'quota', retry_after_seconds: 600 } }));
  const sdk = new EasyAd({ apiKey: 'k', logger: (level) => seen.push(level) });

  assert.equal(await sdk.nextAd({ userId: 1 }), null);
  assert.deepEqual(seen, ['debug']);                 // pas d'avertissement : c'est un cas normal
});

test('une panne réseau ne casse pas le bot', async () => {
  globalThis.fetch = async () => { throw new Error('ECONNREFUSED'); };
  const warnings = [];
  const sdk = new EasyAd({ apiKey: 'k', logger: (level, m) => warnings.push([level, m]) });

  assert.equal(await sdk.nextAd({ userId: 1 }), null);
  assert.equal(warnings[0][0], 'warn');
});

test('throwOnError laisse l\'appelant décider', async () => {
  globalThis.fetch = async () => { throw new Error('ECONNREFUSED'); };
  const sdk = new EasyAd({ apiKey: 'k', throwOnError: true });
  await assert.rejects(() => sdk.nextAd({ userId: 1 }), EasyAdError);
});

test('une clé invalide est signalée', async () => {
  withFetch(() => ({ status: 401, body: { error: 'invalid_api_key', message: 'Clé inconnue' } }));
  const sdk = new EasyAd({ apiKey: 'mauvaise', throwOnError: true });
  await assert.rejects(() => sdk.nextAd({ userId: 1 }), (e) => e.code === 'invalid_api_key' && e.status === 401);
});

test('la confirmation appelle la bonne adresse', async () => {
  const calls = withFetch(() => ({ status: 200, body: { status: 'published' } }));
  assert.equal(await new EasyAd({ apiKey: 'k' }).markShown('pl_abc1234567'), true);
  assert.ok(String(calls[0].url).endsWith('/ads/pl_abc1234567/shown'));
});

test('confirmer sans identifiant ne fait rien', async () => {
  const calls = withFetch(() => ({ status: 200, body: {} }));
  assert.equal(await new EasyAd({ apiKey: 'k' }).markShown(''), false);
  assert.equal(calls.length, 0);
});

test('serve() enchaîne demande, envoi et confirmation', async () => {
  const calls = withFetch(({ call }) => (call === 1
    ? { status: 200, body: ADS }
    : { status: 200, body: { status: 'published' } }));

  const sent = [];
  const done = await new EasyAd({ apiKey: 'k' }).serve({
    userId: 5, send: async (ad) => sent.push(ad.placementId),
  });

  assert.equal(done, true);
  assert.deepEqual(sent, ['pl_abc1234567']);
  assert.equal(calls.length, 2);
});

test('si l\'envoi échoue, rien n\'est confirmé — donc rien n\'est facturé', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  const sdk = new EasyAd({ apiKey: 'k' });

  await assert.rejects(() => sdk.serve({ userId: 5, send: async () => { throw new Error('Telegram 403'); } }));
  assert.equal(calls.length, 1);                     // la confirmation n'a pas été envoyée
});

test('serve() sans annonce ne rappelle pas send', async () => {
  withFetch(() => ({ status: 200, body: { ad: null } }));
  let called = false;
  const done = await new EasyAd({ apiKey: 'k' }).serve({ userId: 5, send: async () => { called = true; } });
  assert.equal(done, false);
  assert.equal(called, false);
});

test('la clé part dans l\'en-tête Authorization', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  await new EasyAd({ apiKey: 'ea_live_secret' }).nextAd({ userId: 1 });
  assert.equal(calls[0].init.headers.Authorization, 'Bearer ea_live_secret');
});

test('l\'adresse de base peut être remplacée pour un environnement de test', async () => {
  const calls = withFetch(() => ({ status: 200, body: ADS }));
  await new EasyAd({ apiKey: 'k', baseUrl: 'https://api.test.local/api/v1/sdk/bot/' }).nextAd({ userId: 1 });
  assert.equal(calls[0].url, 'https://api.test.local/api/v1/sdk/bot/ads/next');
});

test('health renvoie la réponse du serveur', async () => {
  withFetch(() => ({ status: 200, body: { ok: true, bot: { name: 'Mon bot' } } }));
  const h = await new EasyAd({ apiKey: 'k' }).health();
  assert.equal(h.bot.name, 'Mon bot');
});
