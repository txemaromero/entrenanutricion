import { expect, test, type APIRequestContext } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, login } from './helpers';

const accessToken = async (request: APIRequestContext) => {
  const session = await request.post('/api/v1/auth/login', {
    data: { email: DEMO.activeClient, password: DEMO_PASSWORD },
  });
  return ((await session.json()) as { access: string }).access;
};

/**
 * Needs the production build (the service worker serves the app without a network):
 * E2E_PREVIEW=1. Skipped on the dev server.
 */
test('the client follows the workout without coverage and the marks are sent later', async ({
  page,
  context,
}) => {
  const response = await page.goto('/welcome');
  test.skip(!response?.headers()['content-security-policy'], 'needs the production build');

  await login(page, DEMO.activeClient);
  // Once the service worker is active, a reload is always served (and cached) by it.
  await page.evaluate(() => navigator.serviceWorker.ready.then(() => true));
  const available = page
    .locator('[data-testid^="plan-workout-"][data-status="available"]')
    .filter({ visible: true });
  await available.click();
  await expect(page).toHaveURL(/\/workouts\/\d+$/);
  const workoutId = Number(/\/workouts\/(\d+)$/.exec(page.url())![1]);
  // Once more through the service worker, so every file of the app is in its cache.
  await page.reload();
  await expect(byTestId(page, 'day-progress')).toBeVisible();

  const api = page.request;
  const token = await accessToken(api);
  const headers = { Authorization: `Bearer ${token}` };
  const dayOnServer = async () =>
    (await (
      await api.get(`/api/v1/me/training-plan/workouts/${workoutId}`, { headers })
    ).json()) as { exercises: { id: number; order: number; completed: boolean }[] };
  const before = await dayOnServer();
  const target = before.exercises.find((exercise) => !exercise.completed);
  test.skip(!target, 'every exercise of the available workout is already marked');

  try {
    await context.setOffline(true);
    await page.reload();
    await expect(byTestId(page, 'offline-banner')).toBeVisible();
    await expect(byTestId(page, 'day-progress')).toBeVisible();

    await byTestId(page, `check-exercise-${target!.order}`).click();
    await expect(byTestId(page, 'offline-banner')).toContainText('1 ejercicio pendiente');
    await expect(byTestId(page, 'complete-workout')).toHaveAttribute('aria-disabled', 'true');

    await context.setOffline(false);
    await expect(page.getByText('Ejercicios sincronizados')).toBeVisible();
    await expect(byTestId(page, 'offline-banner')).toHaveCount(0);
    const after = await dayOnServer();
    expect(after.exercises.find((exercise) => exercise.id === target!.id)?.completed).toBe(true);
  } finally {
    await context.setOffline(false);
    await api.put(`/api/v1/me/training-plan/workouts/${workoutId}/exercises/${target!.id}`, {
      headers,
      data: { completed: false },
    });
  }
});
