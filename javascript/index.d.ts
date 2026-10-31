// Types de @easyyad/bot-sdk

export interface EasyAdOptions {
  /** Clé secrète du bot (ea_live_…), dans votre espace EasyAd → Bots → Clé d'intégration. */
  apiKey: string;
  /** Pour un environnement de test. Défaut : https://api.easyyad.com/api/v1/sdk/bot */
  baseUrl?: string;
  /** Délai maximal d'un appel (défaut 4000 ms). */
  timeoutMs?: number;
  /** true pour recevoir les erreurs au lieu d'un simple `null`. */
  throwOnError?: boolean;
  /** Sel du hachage des identifiants utilisateurs (défaut : la clé). */
  userSalt?: string;
  logger?: (level: string, message: string, extra?: Record<string, unknown>) => void;
}

export interface EasyAdAd {
  placementId: string;
  text: string;
  parseMode: 'HTML';
  replyMarkup: { inline_keyboard: Array<Array<{ text: string; url: string; style?: string }>> };
  imageUrl: string | null;
  label: string;
  confirmWithinSeconds: number;
}

export interface NextAdParams {
  userId: string | number;
  locale?: string;
}

export declare class EasyAdError extends Error {
  status: number;
  code: string;
  retryAfterSeconds: number | null;
  constructor(message: string, extra?: { status?: number; code?: string; retryAfterSeconds?: number | null });
}

export declare class EasyAd {
  constructor(options: EasyAdOptions);
  nextAd(params: NextAdParams): Promise<EasyAdAd | null>;
  markShown(placementId: string): Promise<boolean>;
  health(): Promise<Record<string, unknown> | null>;
  serve(params: NextAdParams & { send: (ad: EasyAdAd) => Promise<unknown> }): Promise<boolean>;
}

export default EasyAd;
