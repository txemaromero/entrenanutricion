import { expect, test } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, login } from './helpers';

const TUE = 1;
const THU = 3;
const SAT = 5;

// The demo client keeps the recommended days (3 a week) for the other specs.
test.afterEach(async ({ request }) => {
  const session = await request.post('/api/v1/auth/login', {
    data: { email: DEMO.activeClient, password: DEMO_PASSWORD },
  });
  const { access } = (await session.json()) as { access: string };
  await request.put('/api/v1/me/training-days', {
    data: { days: [] },
    headers: { Authorization: `Bearer ${access}` },
  });
});

test('the client picks the training days and the plan follows them', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await expect(byTestId(page, 'training-days')).toContainText('Días recomendados');

  await byTestId(page, 'training-days-edit').click();
  const modal = page.getByTestId('training-days-modal');
  for (const day of [0, 2, 4]) await modal.getByTestId(`weekday-${day}`).click();
  for (const day of [TUE, THU, SAT]) await modal.getByTestId(`weekday-${day}`).click();
  await expect(modal.getByTestId(`weekday-${TUE}`)).toHaveAttribute('aria-pressed', 'true');
  await expect(modal.getByRole('status')).toHaveText('3 días seleccionados');
  await modal.getByTestId('training-days-save').click();

  await expect(byTestId(page, 'training-days')).toContainText('Tus días: martes, jueves, sábado');
  const next = page
    .locator('[data-testid^="plan-workout-"][data-status="available"]')
    .filter({ visible: true });
  await expect(next).toContainText(/martes|jueves|sábado/);

  await byTestId(page, 'training-days-edit').click();
  await page.getByTestId('training-days-modal').getByTestId('training-days-default').click();
  await expect(byTestId(page, 'training-days')).toContainText(
    'Días recomendados: lunes, miércoles, viernes',
  );
});

test('at most six days can be chosen', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await byTestId(page, 'training-days-edit').click();
  const modal = page.getByTestId('training-days-modal');

  for (const day of [1, 3, 5]) await modal.getByTestId(`weekday-${day}`).click();

  await expect(modal.getByRole('status')).toHaveText('6 días seleccionados');
  await expect(modal.getByTestId('weekday-6')).toBeDisabled();
  await modal.getByTestId('weekday-0').click();
  await expect(modal.getByTestId('weekday-6')).toBeEnabled();
});
