import { ApiError } from '../api/errors';

/**
 * Offline copies (phase 11): the last training plan, workouts and exercises a client opened,
 * kept in localStorage under the user's id so they can follow the workout without coverage.
 * Everything is removed on logout and when another user signs in on the same device.
 */
const ROOT = 'entrenanutricion.offline';
let owner: number | null = null;

const keyOf = (key: string) => `${ROOT}.${owner}.${key}`;

const safely = <T>(action: () => T, fallback: T): T => {
  try {
    return action();
  } catch {
    return fallback; // storage unavailable or full: the app simply works online only
  }
};

export const offlineStore = {
  /** Whose copies are read and written; null disables the store. */
  setOwner(userId: number | null) {
    owner = userId;
  },

  owner: () => owner,

  read<T>(key: string): T | null {
    if (owner === null) return null;
    return safely(() => {
      const raw = window.localStorage.getItem(keyOf(key));
      return raw === null ? null : (JSON.parse(raw) as T);
    }, null);
  },

  write(key: string, value: unknown) {
    if (owner === null) return;
    safely(() => window.localStorage.setItem(keyOf(key), JSON.stringify(value)), undefined);
  },

  /** Remove every offline copy of every user (logout, another user signs in). */
  clearAll() {
    safely(() => {
      Object.keys(window.localStorage)
        .filter((key) => key.startsWith(`${ROOT}.`))
        .forEach((key) => window.localStorage.removeItem(key));
    }, undefined);
  },
};

export const isNetworkError = (error: unknown): boolean =>
  error instanceof ApiError && error.code === 'network_error';

/** Fresh data when online (and keep a copy); the last copy when the network is down. */
export const withOfflineCopy =
  <T>(key: string, load: () => Promise<T>) =>
  async (): Promise<T> => {
    try {
      const data = await load();
      offlineStore.write(key, data);
      return data;
    } catch (error) {
      const copy = isNetworkError(error) ? offlineStore.read<T>(key) : null;
      if (copy !== null) return copy;
      throw error;
    }
  };
