# SDK EasyAd

Deux bibliothèques pour afficher des publicités EasyAd dans un bot et être rémunéré :

| Dossier | Paquet | Pour qui |
|---|---|---|
| `javascript/` | `@easyad/bot-sdk` | Node 18+, grammY, Telegraf, telegram-bot-api |
| `python/` | `easyad` | Python 3.9+, pyTelegramBotAPI, aiogram, python-telegram-bot |

Les deux exposent la même chose : `nextAd` / `next_ad`, `markShown` / `mark_shown`, `serve`, `health`.

## L'API derrière

```
POST /api/v1/sdk/bot/ads/next           → une annonce, ou { "ad": null }
POST /api/v1/sdk/bot/ads/{id}/shown     → confirme l'envoi ; c'est ce qui déclenche la rémunération
GET  /api/v1/sdk/bot/health             → vérifie la clé et renvoie les réglages du bot
```

Authentification : `Authorization: Bearer <votre clé EasyAd>`.

Si vous préférez appeler l'API directement, c'est tout ce qu'il y a à savoir — les SDK ne font rien
de plus que ces trois appels, le hachage de l'identifiant utilisateur, et un repli silencieux en cas
de panne.

## Tests

```bash
cd javascript && npm test        # 19 tests
cd python && python -m unittest discover -s tests
```

Aucun test ne touche le réseau : le transport est remplacé.
