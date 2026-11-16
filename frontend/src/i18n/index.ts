import i18n, { type Resource } from 'i18next';
import resourcesToBackend from 'i18next-resources-to-backend';
import { initReactI18next } from 'react-i18next';

import { setApiLanguage } from '../api/client';

export const LANGUAGES = ['es', 'en', 'ca'] as const;
export type Language = (typeof LANGUAGES)[number];

const STORAGE_KEY = 'entrenanutricion.language';

const isLanguage = (value: unknown): value is Language =>
  typeof value === 'string' && (LANGUAGES as readonly string[]).includes(value);

export const readStoredLanguage = (): Language | null => {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return isLanguage(value) ? value : null;
  } catch {
    return null;
  }
};

export const storeLanguage = (language: Language): void => {
  try {
    window.localStorage.setItem(STORAGE_KEY, language);
  } catch {
    /* storage unavailable: the choice lasts for this visit only */
  }
};

export const detectLanguage = (): Language => {
  const stored = readStoredLanguage();
  if (stored) return stored;
  const browser = (navigator.language || '').slice(0, 2).toLowerCase();
  return isLanguage(browser) ? browser : 'es';
};

/** Installed app (PWA): one manifest per language, with its description. */
export const MANIFESTS: Record<Language, string> = {
  es: '/manifest.webmanifest',
  en: '/manifest.en.webmanifest',
  ca: '/manifest.ca.webmanifest',
};

i18n.on('languageChanged', (language) => {
  setApiLanguage(language);
  document.documentElement.lang = language;
  if (isLanguage(language)) {
    document.querySelector('link[rel="manifest"]')?.setAttribute('href', MANIFESTS[language]);
    document
      .querySelector('meta[name="description"]')
      ?.setAttribute('content', i18n.t('app.description'));
  }
});

/**
 * Production loads only the active language with a dynamic `import()`; tests pass `resources`.
 */
export const initI18n = (options: { resources?: Resource; lng?: Language } = {}) => {
  if (!options.resources) {
    i18n.use(resourcesToBackend((language: string) => import(`./locales/${language}.json`)));
  }
  return i18n.use(initReactI18next).init({
    lng: options.lng ?? detectLanguage(),
    fallbackLng: 'es',
    supportedLngs: [...LANGUAGES],
    resources: options.resources,
    interpolation: { escapeValue: false },
    react: { useSuspense: true },
  });
};

export default i18n;
