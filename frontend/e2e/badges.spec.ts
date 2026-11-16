import { expect, test } from '@playwright/test';

import { DEMO, byTestId, login } from './helpers';

test('the client sees the badges earned and the pending ones with their progress', async ({
  page,
}) => {
  await login(page, DEMO.activeClient);
  await byTestId(page, 'tab-progress').click();
  await expect(byTestId(page, 'badges-summary')).toContainText(/\d+ de 8 insignias conseguidas/);

  await byTestId(page, 'badges-view').click();
  await expect(page).toHaveURL(/\/app\/progress\/badges$/);
  // The demo client has trained for about three months and logged the weight every week.
  for (const code of ['first_workout', 'workouts_10', 'weight_logs_10']) {
    await expect(byTestId(page, `badge-${code}`)).toHaveAttribute('data-earned', 'true');
  }
  await expect(byTestId(page, 'badge-first_workout')).toContainText('Conseguida el');
  await expect(byTestId(page, 'badge-workouts_100')).toHaveAttribute('data-earned', 'false');
  await expect(byTestId(page, 'badge-workouts_100')).toContainText(/Pendiente · \d+ de 100/);
});
