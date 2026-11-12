"""easyyad — afficher des annonces EasyAd dans votre bot Telegram.

Deux appels suffisent : next_ad() pour demander une annonce, mark_shown() pour confirmer
son envoi (c'est la confirmation qui déclenche votre rémunération). serve() enchaîne les
trois étapes, et une panne d'EasyAd ne casse jamais votre bot : par défaut, tout renvoie None.

Documentation : https://easyyad.com/docs/bots
"""

from .client import Ad, AsyncEasyAd, EasyAd, EasyAdError, hash_user_id

__version__ = "1.0.0"
__all__ = ["Ad", "AsyncEasyAd", "EasyAd", "EasyAdError", "hash_user_id", "__version__"]
