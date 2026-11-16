import { defineConfig, devices } from '@playwright/test';

/**
 * E2E against the real backend with demo data (`manage.py seed_demo`).
 * Locally: E2E_PYTHON=backend/.venv/Scripts/python.exe npm run e2e (servers are reused if running).
 */
const python = process.env.E2E_PYTHON ?? 'python';
/** E2E_PREVIEW=1: build the app and test the production bundle with its headers (CSP included). */
const preview = Boolean(process.env.E2E_PREVIEW);
const baseURL =
  process.env.E2E_BASE_URL ?? (preview ? 'http://127.0.0.1:4173' : 'http://127.0.0.1:5173');

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    locale: 'es-ES',
    timezoneId: 'Europe/Madrid',
    // The app turns Ionic animations off: no page transitions to wait for.
    reducedMotion: 'reduce',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'mobile', use: { ...devices['Pixel 7'] } }],
  webServer: [
    {
      command: `${python} manage.py runserver 127.0.0.1:8000 --noreload`,
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/v1/health',
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        DJANGO_SETTINGS_MODULE: 'config.settings.dev',
        THROTTLE_LOGIN: '1000/min',
        THROTTLE_LOGIN_ACCOUNT: '1000/min',
        THROTTLE_REGISTER: '1000/min',
        THROTTLE_EMAIL_EXISTS: '1000/min',
        THROTTLE_SESSION: '1000/min',
        THROTTLE_DATA_EXPORT: '1000/min',
        THROTTLE_PASSWORD_RESET: '1000/min',
        THROTTLE_UPLOADS: '1000/min',
      },
    },
    preview
      ? {
          command: 'npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort',
          url: baseURL,
          reuseExistingServer: true,
          timeout: 240_000,
        }
      : {
          command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
          url: baseURL,
          reuseExistingServer: true,
          timeout: 120_000,
        },
  ],
});
