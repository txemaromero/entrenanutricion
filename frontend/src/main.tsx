import React from 'react';
import { createRoot } from 'react-dom/client';

import App from './App';
import { initI18n } from './i18n';

void initI18n();

// Error monitoring: production builds with a DSN only (the SDK is a separate chunk).
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;
if (import.meta.env.PROD && sentryDsn) {
  void import('./monitoring').then(({ initMonitoring }) => initMonitoring(sentryDsn));
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// PWA: only in production builds (the dev server must never be cached).
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => undefined);
  });
}
