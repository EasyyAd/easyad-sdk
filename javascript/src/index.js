/**
 * SDK EasyAd pour les bots — JavaScript / TypeScript (Node 18+).
 *
 * Deux appels suffisent : demander une annonce, puis confirmer qu'elle a bien été envoyée.
 * Rien dans ce SDK ne lève d'erreur par défaut : un réseau coupé ou un quota atteint renvoie
 * simplement `null`, pour qu'une panne chez nous ne casse jamais votre bot.
 */

const DEFAULT_BASE = 'https://api.easyyad.com/api/v1/sdk/bot';

export class EasyAdError extends Error {
  constructor(message, { status, code, retryAfterSeconds } = {}) {
    super(message);
    this.name = 'EasyAdError';
    this.status = status ?? 0;
    this.code = code ?? 'unknown';
    this.retryAfterSeconds = retryAfterSeconds ?? null;
  }
}

/** Identifiant d'utilisateur haché : nous n'avons jamais besoin de l'identifiant réel. */
async function hashUserId(value, salt) {
  const { createHash } = await import('node:crypto');
  return createHash('sha256').update(`${salt}:${value}`).digest('hex').slice(0, 32);
}

export class EasyAd {
  /**
   * @param {object} options
   * @param {string} options.apiKey            Clé secrète du bot (ea_live_…).
   * @param {string} [options.baseUrl]         Pour pointer vers un environnement de test.
   * @param {number} [options.timeoutMs=4000]  Au-delà, on renonce : votre bot doit répondre vite.
   * @param {boolean} [options.throwOnError=false] true pour gérer les erreurs vous-même.
   * @param {string} [options.userSalt]        Sel du hachage des identifiants (défaut : la clé).
   * @param {(level: string, message: string, extra?: object) => void} [options.logger]
   */
  constructor({ apiKey, baseUrl = DEFAULT_BASE, timeoutMs = 4000, throwOnError = false, userSalt, logger } = {}) {
    if (!apiKey) throw new EasyAdError('Clé EasyAd manquante : passez { apiKey }.', { code: 'missing_api_key' });
    this.apiKey = apiKey;
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.timeoutMs = timeoutMs;
    this.throwOnError = throwOnError;
    this.userSalt = userSalt || apiKey;
    this.logger = logger || (() => {});
  }

  /**
   * Demande une annonce pour l'utilisateur en face du bot.
   *
   * @param {object} params
   * @param {string|number} params.userId   Identifiant chez vous ; il est haché avant l'envoi.
   * @param {string} [params.locale]        « fr », « en-US »… pour un meilleur ciblage.
   * @returns {Promise<null|{placementId: string, text: string, parseMode: string, replyMarkup: object, imageUrl: ?string, label: string, confirmWithinSeconds: number}>}
   *   `null` quand il n'y a rien à montrer, que l'utilisateur a atteint son quota, ou en cas de problème réseau.
   */
  async nextAd({ userId, locale } = {}) {
    if (userId === undefined || userId === null || userId === '') {
      throw new EasyAdError('userId est requis : il sert à limiter la fréquence par utilisateur.', { code: 'missing_user_id' });
    }

    const userRef = await hashUserId(String(userId), this.userSalt);
    const body = await this.#post('/ads/next', { user_ref: userRef, locale: locale ?? undefined });
    if (!body || !body.ad) return null;

    const ad = body.ad;
    return {
      placementId: ad.placement_id,
      text: ad.text,
      parseMode: ad.parse_mode || 'HTML',
      replyMarkup: ad.reply_markup,
      imageUrl: ad.image_url ?? null,
      label: ad.label,
      confirmWithinSeconds: ad.confirm_within_seconds ?? 1800,
    };
  }

  /**
   * Confirme l'envoi. **À appeler après** que l'annonce est partie : c'est cette confirmation qui
   * déclenche votre rémunération. Sans elle, l'annonce n'est ni facturée ni payée.
   *
   * @returns {Promise<boolean>} true si la confirmation est enregistrée.
   */
  async markShown(placementId) {
    if (!placementId) return false;
    const body = await this.#post(`/ads/${encodeURIComponent(placementId)}/shown`, {});
    return Boolean(body && body.status === 'published');
  }

  /** Vérifie la clé et renvoie les réglages du bot. Pratique au démarrage. */
  async health() {
    return this.#request('GET', '/health');
  }

  /**
   * Raccourci le plus courant : demande une annonce, l'envoie avec votre fonction, confirme.
   * `send` reçoit l'annonce et doit l'envoyer ; s'il lève une erreur, rien n'est confirmé.
   *
   * @param {object} params
   * @param {string|number} params.userId
   * @param {string} [params.locale]
   * @param {(ad: object) => Promise<unknown>} params.send
   * @returns {Promise<boolean>} true si une annonce a été envoyée et confirmée.
   */
  async serve({ userId, locale, send }) {
    const ad = await this.nextAd({ userId, locale });
    if (!ad) return false;

    await send(ad);                      // une erreur ici remonte : pas de confirmation, pas de facturation
    return this.markShown(ad.placementId);
  }

  async #post(path, payload) {
    return this.#request('POST', path, payload);
  }

  async #request(method, path, payload) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(this.baseUrl + path, {
        method,
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          Accept: 'application/json',
          ...(payload ? { 'Content-Type': 'application/json' } : {}),
        },
        body: payload ? JSON.stringify(payload) : undefined,
        signal: controller.signal,
      });

      const text = await response.text();
      let body = null;
      try { body = text ? JSON.parse(text) : null; } catch { /* réponse non JSON */ }

      if (!response.ok) {
        const error = new EasyAdError(body?.message || `EasyAd a répondu ${response.status}.`, {
          status: response.status,
          code: body?.error || `http_${response.status}`,
          retryAfterSeconds: body?.retry_after_seconds ?? null,
        });
        // Un quota atteint est une réponse normale, pas une panne : on n'alarme personne.
        if (error.code === 'frequency_capped') {
          this.logger('debug', 'EasyAd : quota de fréquence atteint pour cet utilisateur.', { code: error.code });
          return null;
        }
        if (this.throwOnError) throw error;
        this.logger('warn', `EasyAd : ${error.message}`, { code: error.code, status: error.status });
        return null;
      }

      return body;
    } catch (e) {
      if (e instanceof EasyAdError) throw e;
      const aborted = e?.name === 'AbortError';
      const error = new EasyAdError(
        aborted ? `EasyAd n'a pas répondu en ${this.timeoutMs} ms.` : `EasyAd est injoignable : ${e?.message || e}`,
        { code: aborted ? 'timeout' : 'network_error' },
      );
      if (this.throwOnError) throw error;
      this.logger('warn', error.message, { code: error.code });
      return null;
    } finally {
      clearTimeout(timer);
    }
  }
}

export default EasyAd;
