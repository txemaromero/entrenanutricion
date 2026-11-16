import axios, { type InternalAxiosRequestConfig } from 'axios';

import { camelizeKeys, snakifyKeys } from './case';
import { toApiError } from './errors';
import { tokens } from './tokens';

export const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1';

let currentLanguage = 'es';
let onSessionExpired: () => void = () => undefined;

export const setApiLanguage = (language: string): void => {
  currentLanguage = language;
};

export const setSessionExpiredHandler = (handler: () => void): void => {
  onSessionExpired = handler;
};

/** CSRF defence of the cookie endpoints: cross-site pages cannot send it without CORS. */
export const APP_HEADERS = { 'X-Requested-With': 'entrenanutricion' };

// withCredentials: the refresh cookie also reaches an API on another origin (CORS allows it).
export const api = axios.create({ baseURL: API_URL, withCredentials: true, headers: APP_HEADERS });

const isFormData = (value: unknown): value is FormData =>
  typeof FormData !== 'undefined' && value instanceof FormData;

api.interceptors.request.use((config) => {
  const access = tokens.getAccess();
  if (access) config.headers.Authorization = `Bearer ${access}`;
  config.headers['Accept-Language'] = currentLanguage;
  if (config.data && !isFormData(config.data)) config.data = snakifyKeys(config.data);
  if (config.params) config.params = snakifyKeys(config.params);
  return config;
});

let refreshing: Promise<string> | null = null;

/** Time for another tab to finish renewing the session, so that the browser has the new cookie. */
const REFRESH_RETRY_DELAY_MS = 1000;

/** The API refused the session. Anything else (no network, 429, 5xx) may pass: it stays open. */
const sessionRejected = (error: unknown): boolean =>
  axios.isAxiosError(error) && [401, 403].includes(error.response?.status ?? 0);

/**
 * New access token from the refresh cookie (rotated by the API); concurrent 401s share a single
 * request. The API only reads the cookie: there is no token to send.
 *
 * Two tabs can send the same cookie at once: the API rotates it for the first one and rejects the
 * second. So a rejection is tried once more, with the cookie the other tab has just received.
 */
const requestRefresh = () =>
  axios.post(`${API_URL}/auth/refresh`, {}, { withCredentials: true, headers: APP_HEADERS });

export const refreshAccessToken = (): Promise<string> => {
  if (!refreshing) {
    refreshing = requestRefresh()
      .catch(async (error: unknown) => {
        if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error;
        await new Promise((resolve) => setTimeout(resolve, REFRESH_RETRY_DELAY_MS));
        return requestRefresh();
      })
      .then(({ data }) => {
        tokens.startSession(data.access as string);
        return data.access as string;
      })
      .finally(() => {
        refreshing = null;
      });
  }
  return refreshing;
};

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

const AUTH_ENDPOINTS = ['/auth/login', '/auth/register', '/auth/refresh', '/auth/logout'];

api.interceptors.response.use(
  (response) => {
    response.data = camelizeKeys(response.data);
    return response;
  },
  async (error) => {
    const config = error.config as RetriableConfig | undefined;
    const isAuthCall = AUTH_ENDPOINTS.some((path) => config?.url?.startsWith(path));
    if (error.response?.status === 401 && config && !config._retried && !isAuthCall) {
      config._retried = true;
      try {
        await refreshAccessToken();
        return api.request(config);
      } catch (refreshError) {
        if (!sessionRejected(refreshError)) throw toApiError(refreshError);
        tokens.clear();
        onSessionExpired();
      }
    }
    throw toApiError(error);
  },
);
