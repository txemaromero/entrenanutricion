import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '../api/auth';
import { refreshAccessToken, setSessionExpiredHandler } from '../api/client';
import { toApiError } from '../api/errors';
import { meApi } from '../api/me';
import { tokens } from '../api/tokens';
import { isNetworkError, offlineStore } from '../offline/store';
import type { Me, RegisterInput } from '../api/types';
import { useAccountLanguage } from './useAccountLanguage';
import { AuthContext, type AuthContextValue } from './useAuth';

/** The signed-in user, kept so that a reload without coverage does not end the session. */
const LAST_USER_KEY = 'entrenanutricion.offline.me';

const rememberUser = (me: Me) => {
  try {
    const previous = JSON.parse(window.localStorage.getItem(LAST_USER_KEY) ?? 'null') as Me | null;
    // Another person on this device: drop the offline copies of the previous one.
    if (previous && previous.id !== me.id) offlineStore.clearAll();
    window.localStorage.setItem(LAST_USER_KEY, JSON.stringify(me));
  } catch {
    /* storage unavailable */
  }
  offlineStore.setOwner(me.id);
};

const lastUser = (): Me | null => {
  try {
    return JSON.parse(window.localStorage.getItem(LAST_USER_KEY) ?? 'null') as Me | null;
  } catch {
    return null;
  }
};

const forgetUser = () => {
  offlineStore.clearAll();
  offlineStore.setOwner(null);
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUserState] = useState<Me | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [sessionExpired, setSessionExpired] = useState(false);

  useEffect(() => {
    setSessionExpiredHandler(() => {
      // Like a logout: nothing of the account stays on the device (shared phones, lost devices).
      // A new sign-in needs the network anyway, and it downloads the copies again.
      forgetUser();
      setUserState(null);
      setSessionExpired(true);
    });
    let cancelled = false;
    const restore = async () => {
      if (tokens.hasSession()) {
        try {
          await refreshAccessToken();
          const me = await meApi.get();
          rememberUser(me);
          if (!cancelled) setUserState(me);
        } catch (error) {
          const failure = toApiError(error);
          // No coverage or too many requests: not the end of the session.
          const temporary =
            isNetworkError(failure) || failure.code === 'throttled' || !navigator.onLine;
          const known = temporary ? lastUser() : null;
          if (known) {
            // No coverage: open the app with the last copies; the API refreshes the session later.
            offlineStore.setOwner(known.id);
            if (!cancelled) setUserState(known);
          } else {
            tokens.clear();
            forgetUser();
          }
        }
      }
      if (!cancelled) setInitializing(false);
    };
    void restore();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string, rememberMe: boolean) => {
    const response = await authApi.login(email, password, rememberMe);
    tokens.startSession(response.access);
    rememberUser(response.user);
    setSessionExpired(false);
    setUserState(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const response = await authApi.register(input);
    tokens.startSession(response.access);
    rememberUser(response.user);
    setSessionExpired(false);
    setUserState(response.user);
    return response.user;
  }, []);

  const logout = useCallback(async () => {
    tokens.clear();
    forgetUser();
    setUserState(null);
    try {
      await authApi.logout();
    } catch {
      /* the session is already closed in this browser */
    }
  }, []);

  const refreshUser = useCallback(async () => {
    if (!tokens.getAccess() && !tokens.hasSession()) return null;
    const me = await meApi.get();
    rememberUser(me);
    setUserState(me);
    return me;
  }, []);

  // The account keeps the language of the app, so the emails (reminders, password) use it.
  const onLanguageSaved = useCallback((me: Me) => {
    rememberUser(me);
    setUserState(me);
  }, []);
  useAccountLanguage(user, onLanguageSaved);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      initializing,
      sessionExpired,
      login,
      register,
      logout,
      refreshUser,
      setUser: setUserState,
    }),
    [user, initializing, sessionExpired, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
