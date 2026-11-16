import { expect, test, type APIRequestContext } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, fill, login } from './helpers';

interface DayExercise {
  id: number;
  order: number;
  completed: boolean;
  logged_sets: { reps: number; weight_kg: number | null }[];
}

const accessToken = async (request: APIRequestContext) => {
  const session = await request.post('/api/v1/auth/login', {
    data: { email: DEMO.activeClient, password: DEMO_PASSWORD },
  });
  return ((await session.json()) as { access: string }).access;
};

test('the client logs the sets done and sees the progression of the exercise', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await page
    .locator('[data-testid^="plan-workout-"][data-status="available"]')
    .filter({ visible: true })
    .click();
  await expect(page).toHaveURL(/\/workouts\/\d+$/);
  const workoutId = Number(/\/workouts\/(\d+)$/.exec(page.url())![1]);

  const api = page.request;
  const headers = { Authorization: `Bearer ${await accessToken(api)}` };
  const exerciseOnServer = async () => {
    const day = (await (
      await api.get(`/api/v1/me/training-plan/workouts/${workoutId}`, { headers })
    ).json()) as { exercises: DayExercise[] };
    return day.exercises.find((exercise) => exercise.order === 1)!;
  };
  const before = await exerciseOnServer();

  try {
    // The demo client has trained before: the editor shows last session's sets.
    await byTestId(page, 'sets-toggle-1').click();
    await expect(byTestId(page, 'last-sets-1')).toContainText('Última vez:');
    await fill(page, 'set-reps-1-0', '7');
    await fill(page, 'set-weight-1-0', '12.5');
    await byTestId(page, 'save-sets-1').click();

    await expect(page.getByText('Series guardadas')).toBeVisible();
    await expect(byTestId(page, 'logged-sets-1')).toContainText('Hecho: 7 × 12,5 kg');
    await expect(byTestId(page, 'check-exercise-1')).toHaveClass(/checkbox-checked/);
    const saved = await exerciseOnServer();
    expect(saved.completed).toBe(true);
    expect(saved.logged_sets[0]).toEqual({ reps: 7, weight_kg: 12.5 });

    // The exercise screen shows the same sets and the history of the exercise.
    await byTestId(page, 'open-exercise-1').click();
    await expect(byTestId(page, 'exercise-name')).toBeVisible();
    await expect(byTestId(page, 'logged-sets-1')).toContainText('Hecho: 7 × 12,5 kg');
    await expect(byTestId(page, 'exercise-progress')).toContainText('Tu progreso');
    await expect(byTestId(page, 'exercise-history')).toBeVisible();

    // Progress › Workout lists the personal records of the weighted exercises.
    await byTestId(page, 'tab-progress').click();
    await byTestId(page, 'segment-workout').click();
    await expect(byTestId(page, 'records-card')).toContainText('Tus récords');
    await expect(byTestId(page, 'records-card')).toContainText(/\d+ × [\d,]+ kg/);
  } finally {
    await api.put(`/api/v1/me/training-plan/workouts/${workoutId}/exercises/${before.id}`, {
      headers,
      data: { completed: before.completed, sets: before.logged_sets },
    });
  }
});
