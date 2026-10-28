"""Client HTTP du SDK EasyAd : version synchrone et version asynchrone."""

from __future__ import annotations

import hashlib
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

DEFAULT_BASE = "https://api.easyyad.com/api/v1/sdk/bot"
LOGGER = logging.getLogger("easyyad")


class EasyAdError(Exception):
    """Erreur renvoyée par EasyAd, ou impossibilité de le joindre."""

    def __init__(self, message: str, *, status: int = 0, code: str = "unknown",
                 retry_after_seconds: Optional[int] = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class Ad:
    """Une annonce prête à envoyer."""

    placement_id: str
    text: str
    reply_markup: Dict[str, Any]
    parse_mode: str = "HTML"
    image_url: Optional[str] = None
    label: str = "#Ad #EasyAd"
    confirm_within_seconds: int = 1800

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "Ad":
        return cls(
            placement_id=payload["placement_id"],
            text=payload["text"],
            reply_markup=payload.get("reply_markup") or {},
            parse_mode=payload.get("parse_mode") or "HTML",
            image_url=payload.get("image_url"),
            label=payload.get("label") or "#Ad #EasyAd",
            confirm_within_seconds=int(payload.get("confirm_within_seconds") or 1800),
        )


def hash_user_id(user_id: Any, salt: str) -> str:
    """Empreinte stable d'un identifiant : nous n'avons jamais besoin de l'identifiant réel."""
    digest = hashlib.sha256(f"{salt}:{user_id}".encode("utf-8")).hexdigest()
    return digest[:32]


class _Base:
    """Réglages et traitement des réponses, partagés par les deux clients."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE,
        timeout: float = 4.0,
        raise_on_error: bool = False,
        user_salt: Optional[str] = None,
    ) -> None:
        if not api_key:
            raise EasyAdError("Clé EasyAd manquante : passez api_key=…", code="missing_api_key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.raise_on_error = raise_on_error
        self.user_salt = user_salt or api_key

    # -- préparation ----------------------------------------------------

    def _headers(self, with_body: bool) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        if with_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _next_payload(self, user_id: Any, locale: Optional[str]) -> Dict[str, Any]:
        if user_id is None or user_id == "":
            raise EasyAdError(
                "user_id est requis : il sert à limiter la fréquence par utilisateur.",
                code="missing_user_id",
            )
        payload: Dict[str, Any] = {"user_ref": hash_user_id(user_id, self.user_salt)}
        if locale:
            payload["locale"] = locale
        return payload

    # -- traitement des réponses ----------------------------------------

    def _handle(self, status: int, text: str) -> Optional[Dict[str, Any]]:
        body: Optional[Dict[str, Any]]
        try:
            body = json.loads(text) if text else None
        except ValueError:
            body = None

        if status >= 400:
            code = (body or {}).get("error") or f"http_{status}"
            message = (body or {}).get("message") or f"EasyAd a répondu {status}."
            error = EasyAdError(
                message, status=status, code=code,
                retry_after_seconds=(body or {}).get("retry_after_seconds"),
            )
            # Un quota atteint est une réponse normale, pas une panne.
            if code == "frequency_capped":
                LOGGER.debug("EasyAd : quota de fréquence atteint pour cet utilisateur.")
                return None
            if self.raise_on_error:
                raise error
            LOGGER.warning("EasyAd : %s (%s)", message, code)
            return None

        return body

    def _failure(self, exc: BaseException) -> None:
        timeout = isinstance(exc, (TimeoutError, urllib.error.URLError)) and "timed out" in str(exc).lower()
        error = EasyAdError(
            f"EasyAd n'a pas répondu en {self.timeout} s." if timeout else f"EasyAd est injoignable : {exc}",
            code="timeout" if timeout else "network_error",
        )
        if self.raise_on_error:
            raise error
        LOGGER.warning("%s", error)
        return None

    @staticmethod
    def _ad_from(body: Optional[Dict[str, Any]]) -> Optional[Ad]:
        if not body or not body.get("ad"):
            return None
        return Ad.from_payload(body["ad"])


class EasyAd(_Base):
    """Client synchrone, sans dépendance : il n'utilise que la bibliothèque standard."""

    def next_ad(self, *, user_id: Any, locale: Optional[str] = None) -> Optional[Ad]:
        """Une annonce à montrer, ou ``None`` : rien à montrer, quota atteint, ou souci réseau."""
        return self._ad_from(self._request("POST", "/ads/next", self._next_payload(user_id, locale)))

    def mark_shown(self, placement_id: str) -> bool:
        """À appeler **après** l'envoi : c'est cette confirmation qui déclenche votre rémunération."""
        if not placement_id:
            return False
        quoted = urllib.parse.quote(placement_id, safe="")
        body = self._request("POST", f"/ads/{quoted}/shown", {})
        return bool(body and body.get("status") == "published")

    def health(self) -> Optional[Dict[str, Any]]:
        """Vérifie la clé et renvoie les réglages du bot. Pratique au démarrage."""
        return self._request("GET", "/health", None)

    def serve(self, *, user_id: Any, send: Callable[[Ad], Any], locale: Optional[str] = None) -> bool:
        """
        Raccourci : demande, envoie via ``send``, confirme.

        Si ``send`` lève une exception, rien n'est confirmé — donc rien n'est facturé ni payé.
        """
        ad = self.next_ad(user_id=user_id, locale=locale)
        if ad is None:
            return False
        send(ad)
        return self.mark_shown(ad.placement_id)

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.base_url + path, data=data, method=method, headers=self._headers(payload is not None)
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return self._handle(response.status, response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:            # réponse reçue, mais code d'erreur
            return self._handle(exc.code, exc.read().decode("utf-8", errors="replace"))
        except EasyAdError:
            raise
        except Exception as exc:                          # réseau, DNS, TLS, délai dépassé
            return self._failure(exc)


class AsyncEasyAd(_Base):
    """
    Client asynchrone pour aiogram, python-telegram-bot et autres bots async.

    Nécessite ``httpx`` ou ``aiohttp``. Si aucune des deux n'est installée, l'erreur le dit
    clairement au démarrage plutôt qu'au premier appel en production.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._client_factory = self._detect_backend()

    async def next_ad(self, *, user_id: Any, locale: Optional[str] = None) -> Optional[Ad]:
        return self._ad_from(await self._request("POST", "/ads/next", self._next_payload(user_id, locale)))

    async def mark_shown(self, placement_id: str) -> bool:
        if not placement_id:
            return False
        quoted = urllib.parse.quote(placement_id, safe="")
        body = await self._request("POST", f"/ads/{quoted}/shown", {})
        return bool(body and body.get("status") == "published")

    async def health(self) -> Optional[Dict[str, Any]]:
        return await self._request("GET", "/health", None)

    async def serve(
        self, *, user_id: Any, send: Callable[[Ad], Awaitable[Any]], locale: Optional[str] = None
    ) -> bool:
        ad = await self.next_ad(user_id=user_id, locale=locale)
        if ad is None:
            return False
        await send(ad)
        return await self.mark_shown(ad.placement_id)

    def _detect_backend(self) -> str:
        try:
            import httpx  # noqa: F401
            return "httpx"
        except ImportError:
            pass
        try:
            import aiohttp  # noqa: F401
            return "aiohttp"
        except ImportError as exc:
            raise EasyAdError(
                "AsyncEasyAd a besoin de httpx ou aiohttp : pip install httpx",
                code="missing_dependency",
            ) from exc

    async def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        url = self.base_url + path
        headers = self._headers(payload is not None)

        try:
            if self._client_factory == "httpx":
                import httpx

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, json=payload, headers=headers)
                    return self._handle(response.status_code, response.text)

            import aiohttp

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(method, url, json=payload, headers=headers) as response:
                    return self._handle(response.status, await response.text())
        except EasyAdError:
            raise
        except Exception as exc:
            return self._failure(exc)
