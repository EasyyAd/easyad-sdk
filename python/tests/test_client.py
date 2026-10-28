"""Tests du SDK Python : aucun appel réseau réel, le transport est remplacé."""

import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from easyad import Ad, EasyAd, EasyAdError, hash_user_id  # noqa: E402

AD_PAYLOAD = {
    "ad": {
        "placement_id": "pl_abc1234567",
        "text": "<b>Offre</b>\n\nTexte\n\n#Ad #EasyAd",
        "parse_mode": "HTML",
        "reply_markup": {"inline_keyboard": [[{"text": "Découvrir", "url": "https://go.easyyad.com/r/xyz"}]]},
        "image_url": None,
        "label": "#Ad #EasyAd",
        "confirm_within_seconds": 1800,
    }
}


class FakeResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = json.dumps(body).encode() if body is not None else b""

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def patch_urlopen(responses):
    """Remplace urlopen ; `responses` est une liste de (status, body) ou d'exceptions."""
    calls = []
    queue = list(responses)

    def fake(request, timeout=None):
        calls.append({
            "url": request.full_url,
            "method": request.method,
            "headers": dict(request.headers),
            "body": json.loads(request.data) if request.data else None,
            "timeout": timeout,
        })
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, BaseException):
            raise item
        return FakeResponse(*item)

    return mock.patch("urllib.request.urlopen", side_effect=fake), calls


class TestKeyAndHashing(unittest.TestCase):
    def test_la_cle_est_obligatoire(self):
        with self.assertRaises(EasyAdError):
            EasyAd(api_key="")

    def test_l_identifiant_ne_quitte_jamais_le_bot_en_clair(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            EasyAd(api_key="ea_live_test").next_ad(user_id=123456789)

        sent = calls[0]["body"]["user_ref"]
        self.assertEqual(len(sent), 32)
        self.assertNotIn("123456789", sent)

    def test_la_meme_personne_donne_la_meme_empreinte(self):
        self.assertEqual(hash_user_id(7, "sel"), hash_user_id(7, "sel"))
        self.assertNotEqual(hash_user_id(7, "sel-a"), hash_user_id(7, "sel-b"))


class TestNextAd(unittest.TestCase):
    def test_une_annonce_est_renvoyee_en_objet(self):
        patch, _ = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            ad = EasyAd(api_key="k").next_ad(user_id=1, locale="fr")

        self.assertIsInstance(ad, Ad)
        self.assertEqual(ad.placement_id, "pl_abc1234567")
        self.assertEqual(ad.parse_mode, "HTML")
        self.assertIsNone(ad.image_url)

    def test_la_langue_est_transmise(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            EasyAd(api_key="k").next_ad(user_id=1, locale="fr")
        self.assertEqual(calls[0]["body"]["locale"], "fr")

    def test_sans_langue_le_champ_est_absent(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            EasyAd(api_key="k").next_ad(user_id=1)
        self.assertNotIn("locale", calls[0]["body"])

    def test_user_id_est_exige(self):
        patch, _ = patch_urlopen([(200, AD_PAYLOAD)])
        with patch, self.assertRaises(EasyAdError):
            EasyAd(api_key="k").next_ad(user_id=None)

    def test_aucune_annonce_renvoie_none(self):
        patch, _ = patch_urlopen([(200, {"ad": None, "reason": "no_fill"})])
        with patch:
            self.assertIsNone(EasyAd(api_key="k").next_ad(user_id=1))

    def test_la_cle_part_dans_l_entete_authorization(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            EasyAd(api_key="ea_live_secret").next_ad(user_id=1)
        self.assertEqual(calls[0]["headers"]["Authorization"], "Bearer ea_live_secret")

    def test_l_adresse_de_base_peut_etre_remplacee(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])
        with patch:
            EasyAd(api_key="k", base_url="https://api.test.local/sdk/bot/").next_ad(user_id=1)
        self.assertEqual(calls[0]["url"], "https://api.test.local/sdk/bot/ads/next")


class TestErrors(unittest.TestCase):
    def test_un_quota_atteint_renvoie_none_sans_exception(self):
        err = urllib.error.HTTPError(
            "u", 429, "Too Many", {},
            __import__("io").BytesIO(json.dumps({"error": "frequency_capped", "message": "quota"}).encode()),
        )
        patch, _ = patch_urlopen([err])
        with patch:
            self.assertIsNone(EasyAd(api_key="k").next_ad(user_id=1))

    def test_une_panne_reseau_ne_casse_pas_le_bot(self):
        patch, _ = patch_urlopen([urllib.error.URLError("ECONNREFUSED")])
        with patch:
            self.assertIsNone(EasyAd(api_key="k").next_ad(user_id=1))

    def test_raise_on_error_laisse_l_appelant_decider(self):
        patch, _ = patch_urlopen([urllib.error.URLError("ECONNREFUSED")])
        with patch, self.assertRaises(EasyAdError):
            EasyAd(api_key="k", raise_on_error=True).next_ad(user_id=1)

    def test_une_cle_invalide_est_signalee(self):
        err = urllib.error.HTTPError(
            "u", 401, "Unauthorized", {},
            __import__("io").BytesIO(json.dumps({"error": "invalid_api_key", "message": "Clé inconnue"}).encode()),
        )
        patch, _ = patch_urlopen([err])
        with patch, self.assertRaises(EasyAdError) as ctx:
            EasyAd(api_key="mauvaise", raise_on_error=True).next_ad(user_id=1)

        self.assertEqual(ctx.exception.code, "invalid_api_key")
        self.assertEqual(ctx.exception.status, 401)


class TestMarkShown(unittest.TestCase):
    def test_la_confirmation_appelle_la_bonne_adresse(self):
        patch, calls = patch_urlopen([(200, {"status": "published"})])
        with patch:
            self.assertTrue(EasyAd(api_key="k").mark_shown("pl_abc1234567"))
        self.assertTrue(calls[0]["url"].endswith("/ads/pl_abc1234567/shown"))

    def test_confirmer_sans_identifiant_ne_fait_rien(self):
        patch, calls = patch_urlopen([(200, {})])
        with patch:
            self.assertFalse(EasyAd(api_key="k").mark_shown(""))
        self.assertEqual(calls, [])


class TestServe(unittest.TestCase):
    def test_serve_enchaine_demande_envoi_et_confirmation(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD), (200, {"status": "published"})])
        sent = []
        with patch:
            done = EasyAd(api_key="k").serve(user_id=5, send=lambda ad: sent.append(ad.placement_id))

        self.assertTrue(done)
        self.assertEqual(sent, ["pl_abc1234567"])
        self.assertEqual(len(calls), 2)

    def test_si_l_envoi_echoue_rien_n_est_confirme(self):
        patch, calls = patch_urlopen([(200, AD_PAYLOAD)])

        def boom(ad):
            raise RuntimeError("Telegram 403")

        with patch, self.assertRaises(RuntimeError):
            EasyAd(api_key="k").serve(user_id=5, send=boom)

        self.assertEqual(len(calls), 1)      # la confirmation n'est jamais partie

    def test_serve_sans_annonce_ne_rappelle_pas_send(self):
        patch, _ = patch_urlopen([(200, {"ad": None})])
        called = []
        with patch:
            done = EasyAd(api_key="k").serve(user_id=5, send=lambda ad: called.append(1))
        self.assertFalse(done)
        self.assertEqual(called, [])


class TestHealth(unittest.TestCase):
    def test_health_renvoie_la_reponse_du_serveur(self):
        patch, calls = patch_urlopen([(200, {"ok": True, "bot": {"name": "Mon bot"}})])
        with patch:
            body = EasyAd(api_key="k").health()
        self.assertEqual(body["bot"]["name"], "Mon bot")
        self.assertEqual(calls[0]["method"], "GET")
        self.assertIsNone(calls[0]["body"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
