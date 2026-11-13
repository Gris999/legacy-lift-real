/** Browser-independent session persistence rules (also used by regression tests). */
export const AUTH_STORAGE_KEY = 'legacylift_auth_v2';
export const LEGACY_AUTH_STORAGE_KEY = 'legacylift_session';
export const DEFAULT_SESSION_MILLIS = 12 * 60 * 60 * 1000;

export interface SessionUser {
  username: string;
  email?: string;
  id?: string;
}

export interface StoredSession {
  access_token: string;
  expires_at: string;
  user: SessionUser | null;
}

export interface StoragePort {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

function validToken(value: unknown): value is string {
  return typeof value === 'string' && value.length >= 32 && value.length <= 256;
}

export function createStoredSession(
  access_token: string,
  expires_at?: string,
  user: SessionUser | null = null,
  now = Date.now()
): StoredSession {
  if (!validToken(access_token)) throw new Error('El servidor devolvió una sesión inválida');
  const expiration = expires_at ? Date.parse(expires_at) : now + DEFAULT_SESSION_MILLIS;
  if (!Number.isFinite(expiration) || expiration <= now) throw new Error('La sesión ya ha expirado');
  return {access_token, expires_at: new Date(expiration).toISOString(), user};
}

export function parseStoredSession(raw: string | null, now = Date.now()): StoredSession | null {
  if (!raw) return null;
  try {
    const decoded: unknown = JSON.parse(raw);
    if (!decoded || typeof decoded !== 'object') return null;
    const obj = decoded as Record<string, unknown>;
    if (!validToken(obj['access_token']) || typeof obj['expires_at'] !== 'string') return null;
    if (!(Date.parse(obj['expires_at']) > now)) return null;
    let user: SessionUser | null = null;
    if (obj['user'] && typeof obj['user'] === 'object') {
      const entry = obj['user'] as Record<string, unknown>;
      if (typeof entry['username'] === 'string' && entry['username'].length <= 100) {
        user = {username: entry['username']};
        if (typeof entry['email'] === 'string') user.email = entry['email'];
        if (typeof entry['id'] === 'string') user.id = entry['id'];
      }
    }
    return {access_token: obj['access_token'], expires_at: obj['expires_at'], user};
  } catch { return null; }
}

/** Migrate sessions created by Sprint 1 without prompting a second login. */
export function restoreStoredSession(
  persistent: StoragePort | null,
  legacy: StoragePort | null,
  now = Date.now()
): StoredSession | null {
  if (persistent) {
    const raw = persistent.getItem(AUTH_STORAGE_KEY);
    const stored = parseStoredSession(raw, now);
    if (stored) {
      legacy?.removeItem(LEGACY_AUTH_STORAGE_KEY);
      return stored;
    }
    if (raw) persistent.removeItem(AUTH_STORAGE_KEY);
  }
  const oldToken = legacy?.getItem(LEGACY_AUTH_STORAGE_KEY);
  if (!validToken(oldToken)) return null;
  const migrated = createStoredSession(oldToken, undefined, null, now);
  persistent?.setItem(AUTH_STORAGE_KEY, JSON.stringify(migrated));
  legacy?.removeItem(LEGACY_AUTH_STORAGE_KEY);
  return migrated;
}
