"""
SDK EasyAd pour les bots — Python 3.9+.

Deux appels suffisent : demander une annonce, puis confirmer qu'elle a bien été envoyée.
Par défaut, rien ne lève d'exception : un réseau coupé ou un quota atteint renvoie simplement
``None``, pour qu'une panne chez nous ne casse jamais votre bot.

    from easyad import EasyAd

    easyad = EasyAd(api_key=os.environ["EASYAD_API_KEY"])

    ad = easyad.next_ad(user_id=message.from_user.id, locale=message.from_user.language_code)
    if ad:
        await bot.send_message(chat_id, ad.text, parse_mode="HTML", reply_markup=ad.reply_markup)
        easyad.mark_shown(ad.placement_id)

Une variante asynchrone (``AsyncEasyAd``) est disponible pour aiogram et les bots async.
"""

from .client import AsyncEasyAd, EasyAd, EasyAdError, Ad, hash_user_id

__all__ = ["EasyAd", "AsyncEasyAd", "EasyAdError", "Ad", "hash_user_id"]
__version__ = "1.0.0"
