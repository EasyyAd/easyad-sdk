# SDK EasyAd — publicités pour bots Telegram

Affichez des publicités [EasyAd](https://easyyad.com) dans votre bot Telegram et touchez **50 %**
de ce que l'annonceur paie. Deux appels suffisent, et une panne de notre côté ne casse jamais
votre bot.

> **English** — Show [EasyAd](https://easyyad.com) ads in your Telegram bot and earn **50%** of
> what advertisers pay. Two calls are enough, and an outage on our side never breaks your bot.
> Each package's README has a full English summary.

[![npm](https://img.shields.io/npm/v/%40easyyad%2Fbot-sdk)](https://www.npmjs.com/package/@easyyad/bot-sdk)
[![PyPI](https://img.shields.io/pypi/v/easyyad)](https://pypi.org/project/easyyad/)
[![Licence MIT](https://img.shields.io/badge/licence-MIT-blue)](LICENSE)

| Dossier | Paquet | Pour qui |
|---|---|---|
| [`javascript/`](javascript/) | [`@easyyad/bot-sdk`](https://www.npmjs.com/package/@easyyad/bot-sdk) | Node 18+, grammY, Telegraf, telegram-bot-api |
| [`python/`](python/) | [`easyyad`](https://pypi.org/project/easyyad/) | Python 3.9+, pyTelegramBotAPI, aiogram, python-telegram-bot |

Les deux exposent la même chose : `nextAd` / `next_ad`, `markShown` / `mark_shown`, `serve`, `health`.

## Démarrer en trois lignes

```js
// npm install @easyyad/bot-sdk
import { EasyAd } from '@easyyad/bot-sdk';

const easyad = new EasyAd({ apiKey: process.env.EASYAD_API_KEY });
await easyad.serve({
  userId: ctx.from.id,
  locale: ctx.from.language_code,
  send: (ad) => ctx.reply(ad.text, { parse_mode: 'HTML', reply_markup: ad.replyMarkup }),
});
```

```python
# pip install easyyad
from easyyad import EasyAd

easyad = EasyAd(api_key=os.environ["EASYAD_API_KEY"])
easyad.serve(
    message.from_user.id,
    send=lambda ad: bot.send_message(message.chat.id, ad.text, parse_mode="HTML", reply_markup=ad.reply_markup),
)
```

Votre clé se crée dans votre [espace EasyAd](https://app.easyyad.com), onglet **Bots**.
Pas encore de compte ? Toute clé commençant par `ea_test_` (par exemple `ea_test_demo`)
renvoie une annonce factice : de quoi tester l'intégration sans rien enregistrer ni payer.

## Les principes

- **Votre bot d'abord.** L'annonce s'envoie après la réponse du bot, jamais à la place.
- **Pas payé, pas facturé.** `markShown` ne se confirme qu'après l'envoi réussi : un envoi raté
  ne compte pour personne.
- **Vie privée.** L'identifiant Telegram de l'utilisateur ne nous parvient jamais : le SDK envoie
  une empreinte salée (SHA-256, 32 caractères).
- **Robuste.** Par défaut, toute erreur réseau ou serveur fait simplement renvoyer `null` / `None`,
  et la conversation continue.

## L'API derrière

Les SDK ne font rien de plus que trois appels HTTP, le hachage de l'identifiant utilisateur et un
repli silencieux en cas de panne. Si vous préférez appeler l'API directement :

```
POST /api/v1/sdk/bot/ads/next           → une annonce, ou { "ad": null }
POST /api/v1/sdk/bot/ads/{id}/shown     → confirme l'envoi ; c'est ce qui déclenche la rémunération
GET  /api/v1/sdk/bot/health             → vérifie la clé et renvoie les réglages du bot
```

Authentification : `Authorization: Bearer <votre clé EasyAd>`. Base : `https://api.easyyad.com`.

## Documentation et aide

- Guide complet, avec exemples aiogram, Telegraf et grammY : https://easyyad.com/docs/bots
- Votre tableau de bord : https://app.easyyad.com
- Une question, un souci : support@easyyad.com, ou ouvrez une *issue* ici.

## Contribuer

Les *issues* et *pull requests* sont bienvenues. Lancez les tests avec `npm test` dans
`javascript/` et `python -m unittest discover -s tests` dans `python/` — ils tournent aussi
automatiquement sur chaque *pull request*. Publication des versions : voir
[RELEASING.md](RELEASING.md) (mainteneurs).

## Licence

[MIT](LICENSE) — utilisez, modifiez, redistribuez librement.
