import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeAll } from 'vitest';

import { initI18n } from './i18n';
import ca from './i18n/locales/ca.json';
import en from './i18n/locales/en.json';
import es from './i18n/locales/es.json';

if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }),
  });
}

beforeAll(async () => {
  await initI18n({
    lng: 'es',
    resources: { es: { translation: es }, en: { translation: en }, ca: { translation: ca } },
  });
});

afterEach(() => cleanup());
