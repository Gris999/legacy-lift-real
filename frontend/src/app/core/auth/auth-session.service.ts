import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import {
  AUTH_STORAGE_KEY, LEGACY_AUTH_STORAGE_KEY, StoredSession, SessionUser,
  StoragePort, createStoredSession, restoreStoredSession
} from './session-store';

/** One source of truth for bearer tokens and the identity shown in the shell.
 * Tokens remain bounded by the server's 12-hour expiration and revocation.
 * Future production hardening: replace browser bearer storage with HttpOnly + CSRF cookies.
 */
@Injectable({providedIn: 'root'})
export class AuthSessionService {
  private readonly state = new BehaviorSubject<StoredSession | null>(this.readBrowser());
  readonly changes = this.state.asObservable();

  constructor() {
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', event => {
        if (event.key === AUTH_STORAGE_KEY || event.key === null) {
          this.state.next(this.readBrowser());
        }
      });
    }
  }

  get token(): string | null {
    const item = this.state.value;
    if (item && Date.parse(item.expires_at) <= Date.now()) {
      this.clear(item.access_token);
      return null;
    }
    return item?.access_token ?? null;
  }

  get user(): SessionUser | null { return this.state.value?.user ?? null; }

  save(accessToken: string, expiresAt?: string, user: SessionUser | null = null): void {
    const next = createStoredSession(accessToken, expiresAt, user);
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(next));
      sessionStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
    } catch { /* Browser storage may be unavailable; in-memory session still works. */ }
    this.state.next(next);
  }

  rememberUser(user: SessionUser, expectedToken: string): void {
    const previous = this.state.value;
    if (!previous || previous.access_token !== expectedToken) return;
    const updated = {...previous, user};
    try { localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(updated)); } catch { /* in-memory only */ }
    this.state.next(updated);
  }

  /** Only clear the matching session: a late 401 from an old request must not log out a new user. */
  clear(expectedToken?: string): void {
    if (expectedToken && this.state.value?.access_token !== expectedToken) return;
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      sessionStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
    } catch { /* Private browsing or blocked storage */ }
    this.state.next(null);
  }

  private readBrowser(): StoredSession | null {
    try {
      return restoreStoredSession(
        typeof localStorage === 'undefined' ? null : localStorage as StoragePort,
        typeof sessionStorage === 'undefined' ? null : sessionStorage as StoragePort
      );
    } catch { return null; }
  }
}
