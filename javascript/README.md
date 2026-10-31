# @easyyad/bot-sdk

Affichez des publicités EasyAd dans votre bot Telegram et touchez **50 %** de ce que l'annonceur paie.

> **English** — Show EasyAd ads in your Telegram bot and earn **50%** of what advertisers pay.
> `npm install @easyyad/bot-sdk`, create `new EasyAd({ apiKey })`, then call `easyad.serve({ userId, locale, send })`
> after your bot has answered. Works with ESM (`import`) and CommonJS (`require`), Node 18+. TypeScript types included.
> Full documentation: https://easyyad.com/docs

```bash
npm install @easyyad/bot-sdk
```

## En trois lignes

```js
import { EasyAd } from '@easyyad/bot-sdk';

const easyad = new EasyAd({ apiKey: process.env.EASYAD_API_KEY });
```

Récupérez votre clé dans votre espace EasyAd, onglet **Bots** → votre bot → **Clé d'intégration**.
Elle n'est affichée qu'une fois : nous n'en gardons qu'une empreinte, nous ne pouvons pas vous la
redonner, seulement la remplacer.

## Montrer une annonce

```js
bot.on('message', async (ctx) => {
  await repondreNormalement(ctx);                 // votre bot fait d'abord son travail

  const ad = await easyad.nextAd({
    userId: ctx.from.id,
    locale: ctx.from.language_code,
  });

  if (ad) {
    await ctx.reply(ad.text, { parse_mode: 'HTML', reply_markup: ad.replyMarkup });
    await easyad.markShown(ad.placementId);        // sans cette ligne, vous n'êtes pas payé
  }
});
```

`nextAd` renvoie `null` quand il n'y a rien à montrer, quand cet utilisateur a déjà vu son quota du
jour, ou si EasyAd est momentanément injoignable. Dans les trois cas, votre bot continue comme si
rien ne s'était passé : **une panne chez nous ne doit jamais casser votre bot.**

### Le raccourci `serve()`

```js
await easyad.serve({
  userId: ctx.from.id,
  locale: ctx.from.language_code,
  send: (ad) => ctx.reply(ad.text, { parse_mode: 'HTML', reply_markup: ad.replyMarkup }),
});
```

Demande, envoie, confirme. Si votre `send` échoue, rien n'est confirmé — donc rien ne vous est
compté, et l'annonceur n'est pas facturé.

## Avec une image

```js
if (ad.imageUrl) {
  await ctx.replyWithPhoto(ad.imageUrl, { caption: ad.text, parse_mode: 'HTML', reply_markup: ad.replyMarkup });
} else {
  await ctx.reply(ad.text, { parse_mode: 'HTML', reply_markup: ad.replyMarkup });
}
await easyad.markShown(ad.placementId);
```

## Vérifier l'intégration

```js
console.log(await easyad.health());
// { ok: true, bot: { name: 'Mon bot', status: 'approved', serving: true }, limits: { … } }
```

Appelez-le au démarrage : vous saurez tout de suite si la clé est bonne et si votre bot est approuvé.

## Ce que l'on reçoit de vous

`userId` est **haché avant l'envoi** (SHA-256, tronqué à 32 caractères, salé avec votre clé). Nous ne
voyons jamais l'identifiant Telegram de vos utilisateurs, et comme le sel est votre clé, deux
partenaires ne peuvent pas recouper leurs audiences. Cette empreinte ne sert qu'à une chose : ne pas
montrer trop d'annonces à la même personne.

Vous pouvez choisir votre propre sel avec `userSalt` — gardez-le stable, sinon le plafond de
fréquence repart de zéro à chaque changement.

## Options

| Option | Défaut | À quoi ça sert |
|---|---|---|
| `apiKey` | — | Votre clé secrète. Obligatoire. |
| `baseUrl` | `https://api.easyyad.com/api/v1/sdk/bot` | Pour viser un environnement de test. |
| `timeoutMs` | `4000` | Au-delà, on renonce : votre bot doit rester rapide. |
| `throwOnError` | `false` | `true` pour gérer les erreurs vous-même. |
| `userSalt` | la clé | Sel du hachage des identifiants. |
| `logger` | — | `(level, message, extra) => void`, branchez votre journalisation. |

## Fréquence

Deux limites, réglables dans votre espace EasyAd :

- **annonces par utilisateur et par jour** (3 par défaut) ;
- **délai minimum entre deux annonces** pour la même personne (60 minutes par défaut).

Elles existent pour protéger votre audience : une conversation privée saturée de publicité fait
partir vos utilisateurs, et c'est votre revenu qui disparaît avec eux. Vous pouvez les resserrer
autant que vous voulez.

## Rémunération

Vous êtes payé sur les annonces **confirmées**. Une annonce demandée mais jamais confirmée est
abandonnée au bout de 30 minutes et ne compte pour personne. Les gains apparaissent dans votre
portefeuille après la période de vérification, puis deviennent retirables.

Documentation complète : <https://www.easyyad.com/docs/bots>
