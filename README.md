# SDK EasyAd

Deux bibliothèques pour afficher des publicités EasyAd dans un bot et être rémunéré :

| Dossier | Paquet | Pour qui |
|---|---|---|
| `javascript/` | `@easyyad/bot-sdk` | Node 18+, grammY, Telegraf, telegram-bot-api |
| `python/` | `easyyad` | Python 3.9+, pyTelegramBotAPI, aiogram, python-telegram-bot |

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

## Publication

Elle est automatique : poussez une étiquette de version et GitHub Actions teste puis publie
les deux paquets (une version déjà en ligne est sautée).

```bash
# après avoir monté la version dans javascript/package.json,
# python/pyproject.toml et python/easyyad/__init__.py :
git tag v1.0.1
git push --tags
```

À configurer une seule fois sur le dépôt GitHub :

1. **npm** — créez l'organisation `easyyad` sur npmjs.com (le paquet est `@easyyad/bot-sdk`),
   générez un jeton « Granular Access Token » limité à ce paquet avec le droit *Read and write*,
   et mettez-le dans *Settings → Secrets and variables → Actions* sous le nom `NPM_TOKEN`.
2. **PyPI** — aucun jeton : sur pypi.org → *Your account → Publishing → Add a pending publisher*,
   déclarez le projet `easyyad`, ce dépôt, le fichier `publish.yml` et l'environnement `pypi`.

Le dépôt peut être public sans crainte : licence MIT, aucun secret dedans — les jetons vivent
dans les secrets GitHub, jamais dans le code. `publish.sh` reste une solution de repli manuelle
depuis le serveur.
