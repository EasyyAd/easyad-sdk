# easyad (Python)

Affichez des publicités EasyAd dans votre bot Telegram et touchez **50 %** de ce que l'annonceur paie.

```bash
pip install easyad            # client synchrone, sans dépendance
pip install easyad[async]     # ajoute httpx pour la version asynchrone
```

## En trois lignes

```python
import os
from easyad import EasyAd

easyad = EasyAd(api_key=os.environ["EASYAD_API_KEY"])
```

Récupérez votre clé dans votre espace EasyAd, onglet **Bots** → votre bot → **Clé d'intégration**.
Elle n'est affichée qu'une fois : nous n'en gardons qu'une empreinte, nous ne pouvons pas vous la
redonner, seulement la remplacer.

## Montrer une annonce

```python
ad = easyad.next_ad(user_id=message.from_user.id, locale=message.from_user.language_code)

if ad:
    bot.send_message(
        message.chat.id, ad.text,
        parse_mode="HTML", reply_markup=ad.reply_markup,
    )
    easyad.mark_shown(ad.placement_id)        # sans cette ligne, vous n'êtes pas payé
```

`next_ad` renvoie `None` quand il n'y a rien à montrer, quand cet utilisateur a déjà vu son quota du
jour, ou si EasyAd est momentanément injoignable. Dans les trois cas, votre bot continue comme si
rien ne s'était passé : **une panne chez nous ne doit jamais casser votre bot.**

### Le raccourci `serve()`

```python
easyad.serve(
    user_id=message.from_user.id,
    locale=message.from_user.language_code,
    send=lambda ad: bot.send_message(
        message.chat.id, ad.text, parse_mode="HTML", reply_markup=ad.reply_markup,
    ),
)
```

Demande, envoie, confirme. Si votre fonction `send` lève une exception, rien n'est confirmé — donc
rien ne vous est compté, et l'annonceur n'est pas facturé.

## Bots asynchrones (aiogram, python-telegram-bot)

```python
from easyad import AsyncEasyAd

easyad = AsyncEasyAd(api_key=os.environ["EASYAD_API_KEY"])

@dp.message()
async def handler(message: Message):
    await repondre_normalement(message)

    ad = await easyad.next_ad(user_id=message.from_user.id, locale=message.from_user.language_code)
    if ad:
        await message.answer(ad.text, parse_mode="HTML", reply_markup=ad.reply_markup)
        await easyad.mark_shown(ad.placement_id)
```

`AsyncEasyAd` utilise `httpx` s'il est installé, sinon `aiohttp`. Si aucune des deux n'est présente,
l'erreur arrive à la construction du client — pas au premier appel en production.

## Avec une image

```python
if ad.image_url:
    bot.send_photo(chat_id, ad.image_url, caption=ad.text, parse_mode="HTML", reply_markup=ad.reply_markup)
else:
    bot.send_message(chat_id, ad.text, parse_mode="HTML", reply_markup=ad.reply_markup)

easyad.mark_shown(ad.placement_id)
```

## Vérifier l'intégration

```python
print(easyad.health())
# {'ok': True, 'bot': {'name': 'Mon bot', 'status': 'approved', 'serving': True}, 'limits': {...}}
```

Appelez-le au démarrage : vous saurez tout de suite si la clé est bonne et si votre bot est approuvé.

## Ce que l'on reçoit de vous

`user_id` est **haché avant l'envoi** (SHA-256, tronqué à 32 caractères, salé avec votre clé). Nous ne
voyons jamais l'identifiant Telegram de vos utilisateurs, et comme le sel est votre clé, deux
partenaires ne peuvent pas recouper leurs audiences. Cette empreinte ne sert qu'à une chose : ne pas
montrer trop d'annonces à la même personne.

Vous pouvez choisir votre propre sel avec `user_salt=` — gardez-le stable, sinon le plafond de
fréquence repart de zéro à chaque changement.

## Options

| Option | Défaut | À quoi ça sert |
|---|---|---|
| `api_key` | — | Votre clé secrète. Obligatoire. |
| `base_url` | `https://api.easyyad.com/api/v1/sdk/bot` | Pour viser un environnement de test. |
| `timeout` | `4.0` | Secondes. Au-delà, on renonce : votre bot doit rester rapide. |
| `raise_on_error` | `False` | `True` pour gérer les exceptions vous-même. |
| `user_salt` | la clé | Sel du hachage des identifiants. |

La journalisation passe par le logger standard `easyad` :

```python
import logging
logging.getLogger("easyad").setLevel(logging.DEBUG)
```

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
