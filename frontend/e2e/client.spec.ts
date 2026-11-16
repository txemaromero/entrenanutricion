import { expect, test } from '@playwright/test';

import { DEMO, byTestId, fill, login, registerAndOnboard, uniqueEmail } from './helpers';

test.describe('client', () => {
  test('E2E 1 · register, complete the onboarding and wait for plans', async ({ page }) => {
    await registerAndOnboard(page, uniqueEmail('e2e.registro'));

    await expect(byTestId(page, 'plan-status-title')).toHaveText('Estamos preparando tu plan…');
    await expect(byTestId(page, 'status-training')).toHaveAttribute('data-done', 'false');
    await expect(byTestId(page, 'status-nutrition')).toHaveAttribute('data-done', 'false');
    // Pending clients only see "Plan status" and "Profile".
    await expect(page.locator('ion-tab-button')).toHaveCount(2);
    await page.goto('/app/training');
    await expect(page).toHaveURL(/\/app\/status$/);
  });

  test('registration checks the email live and blocks duplicates', async ({ page }) => {
    await page.goto('/register');
    await fill(page, 'field-email', DEMO.activeClient);
    await byTestId(page, 'field-firstName').locator('input').focus();

    await expect(byTestId(page, 'field-email')).toContainText('Este email ya está registrado.');
    await expect(byTestId(page, 'register-submit')).toHaveAttribute('aria-disabled', 'true');
  });

  test('E2E 3 · complete a whole workout and unlock the next one', async ({ page }) => {
    await login(page, DEMO.activeClient);
    await expect(page).toHaveURL(/\/app\/training$/);

    const cards = page.locator('[data-testid^="plan-workout-"]').filter({ visible: true });
    await expect(cards.first()).toBeVisible();
    const total = await cards.count();
    const available = page
      .locator('[data-testid^="plan-workout-"][data-status="available"]')
      .filter({
        visible: true,
      });
    const order = Number((await available.getAttribute('data-testid'))!.split('-').pop());
    // A locked card does not navigate.
    const locked = page.locator('[data-testid^="plan-workout-"][data-status="locked"]').filter({
      visible: true,
    });
    if ((await locked.count()) > 0) {
      await locked.first().click();
      await expect(page).toHaveURL(/\/app\/training$/);
    }

    await available.click();
    await expect(page).toHaveURL(/\/app\/training\/workouts\/\d+$/);
    const checks = page.locator('[data-testid^="check-exercise-"]').filter({ visible: true });
    await expect(checks.first()).toBeVisible();
    for (let index = 0; index < (await checks.count()); index += 1) {
      const check = checks.nth(index);
      if (!(await check.evaluate((element) => element.classList.contains('checkbox-checked')))) {
        await check.click();
      }
    }
    await expect(byTestId(page, 'day-progress')).toHaveAttribute('data-percent', '100');

    // Checkbox state survives leaving and coming back (regression #4).
    await page.reload();
    await expect(byTestId(page, 'day-progress')).toHaveAttribute('data-percent', '100');

    await byTestId(page, 'complete-workout').click();
    const alert = page.locator('ion-alert');
    await expect(alert).toBeVisible();
    await alert.locator('button').click();

    await expect(page).toHaveURL(/\/app\/training$/);
    const nextOrder = order === total ? 1 : order + 1;
    await expect(byTestId(page, `plan-workout-${nextOrder}`)).toHaveAttribute(
      'data-status',
      'available',
    );
    if (order !== total) {
      await expect(byTestId(page, `plan-workout-${order}`)).toHaveAttribute(
        'data-status',
        'completed',
      );
    }
  });

  test('E2E 4 · adding a weight updates the chart at once', async ({ page }) => {
    await login(page, DEMO.activeClient);
    await byTestId(page, 'tab-progress').click();
    await byTestId(page, 'segment-weight').click();
    const chart = byTestId(page, 'weight-chart');
    await expect(chart).toBeVisible();
    const before = Number(await chart.getAttribute('data-points'));

    // A past day without a record (one record per day; the same day would be updated).
    const day = new Date();
    day.setDate(day.getDate() - (150 + Math.floor(Math.random() * 200)));
    const iso = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, '0')}-${String(
      day.getDate(),
    ).padStart(2, '0')}`;
    await fill(page, 'field-weightKg', '77.7');
    await fill(page, 'field-date', iso);
    await byTestId(page, 'add-weight').click();

    await expect(chart).toHaveAttribute('data-points', String(before + 1));
  });

  test('the active client sees the four tabs, macros and the exercise detail', async ({ page }) => {
    await login(page, DEMO.activeClient);
    await expect(page.locator('ion-tab-button')).toHaveCount(4);

    await byTestId(page, 'tab-nutrition').click();
    await expect(byTestId(page, 'diet-title')).toHaveText('Dieta alta en proteínas');
    await expect(byTestId(page, 'meal-table')).toContainText('Desayuno');

    await byTestId(page, 'tab-training').click();
    await page
      .locator('[data-testid^="plan-workout-"][data-status="available"]')
      .filter({ visible: true })
      .click();
    await byTestId(page, 'open-exercise-1').click();
    await expect(byTestId(page, 'big-circles')).toBeVisible();
    await expect(byTestId(page, 'rest-timer-clock')).toHaveText(/\d\d:\d\d/);
    await byTestId(page, 'exercise-info-button').click();
    await expect(page.locator('ion-modal').getByText('Paso a paso')).toBeVisible();
    await page.getByTestId('exercise-info-close').click();
  });
});
