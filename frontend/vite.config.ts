/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react';
import { defineConfig, loadEnv } from 'vite';

import { SECURITY_HEADERS } from './security-headers.ts';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      // The Host header is kept, so the API builds media URLs on the app's own origin (like nginx).
      proxy: {
        '/api': { target: proxyTarget },
        '/media': { target: proxyTarget },
      },
    },
    // `vite preview` serves the build with the production security headers (CSP included).
    preview: { port: 4173, headers: SECURITY_HEADERS },
    build: {
      rolldownOptions: {
        // Ionic's component modules have no import-time side effects (each component registers
        // itself when first rendered), but the packages do not say so: without this, every
        // component (datetime, pickers, menus…) ends up in the bundle even if unused.
        treeshake: {
          moduleSideEffects: (id: string) =>
            !/node_modules\/@ionic\/(react\/dist|core\/components)\/[^/]+\.js$/.test(id),
        },
        output: {
          // Long-lived vendor chunks: app deploys don't invalidate the (large) Ionic bundle.
          codeSplitting: {
            groups: [
              { name: 'ionic', test: /node_modules[\\/](@ionic|@stencil|ionicons)/ },
              { name: 'charts', test: /node_modules[\\/](chart\.js|react-chartjs-2)/ },
              { name: 'vendor', test: /node_modules/ },
            ],
          },
        },
      },
      // @ionic/react registers every Ionic web component, so its chunk alone exceeds 500 kB.
      chunkSizeWarningLimit: 1400,
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: ['./src/setupTests.ts'],
      include: ['src/**/*.test.{ts,tsx}', 'tests/**/*.test.{ts,tsx}'],
      css: false,
      server: { deps: { inline: [/@ionic/, /ionicons/] } },
    },
  };
});
