/**
 * Session tokens. The access token only lives in memory. The refresh token is an httpOnly cookie
 * set by the API: JavaScript never sees it, so an XSS cannot steal it. A non-secret flag in
 * localStorage only says "there may be a session to restore", so anonymous visits skip the call.
 * Storage can be unavailable (private mode, blocked site data), so every access is guarded.
 */

const SESSION_FLAG = 'entrenanutricion.session';
/** Where versions before the cookie kept the refresh token: never read again, only deleted. */
const LEGACY_REFRESH_KEY = 'entrenanutricion.refresh';

let accessToken: string | null = null;

const read = (storage: () => Storage, key: string): string | null => {
  try {
    return storage().getItem(key);
  } catch {
    return null;
  }
};

const write = (storage: () => Storage, key: string, value: string | null): void => {
  try {
    if (value === null) storage().removeItem(key);
    else storage().setItem(key, value);
  } catch {
    /* storage unavailable: the session simply won't be restored after a reload */
  }
};

const local = () => window.localStorage;
const session = () => window.sessionStorage;

const forgetLegacyRefresh = (): void => {
  write(local, LEGACY_REFRESH_KEY, null);
  write(session, LEGACY_REFRESH_KEY, null);
};

export const tokens = {
  getAccess: (): string | null => accessToken,

  setAccess: (token: string | null): void => {
    accessToken = token;
  },

  /** A session was open in this browser (the cookie decides whether it is still valid). */
  hasSession: (): boolean => read(local, SESSION_FLAG) !== null,

  /** Call after every login or refresh: the access token and the flag. */
  startSession: (access: string): void => {
    accessToken = access;
    write(local, SESSION_FLAG, '1');
    forgetLegacyRefresh();
  },

  clear: (): void => {
    accessToken = null;
    write(local, SESSION_FLAG, null);
    forgetLegacyRefresh();
  },
};
