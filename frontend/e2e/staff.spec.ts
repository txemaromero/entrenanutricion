import { expect, test } from '@playwright/test';

import {
  DEMO,
  acceptAlert,
  byTestId,
  chooseOption,
  fill,
  login,
  registerAndOnboard,
  search,
  switchUser,
  searchPending,
  uniqueEmail,
  clickOne,
} from './helpers';

const pendingRow = (page: import('@playwright/test').Page, email: string) =>
  page
    .locator('[data-testid^="pending-user-"]')
    .filter({ visible: true })
    .filter({ hasText: email });

test.describe('management', () => {
  test('E2E 2 · trainer and nutritionist assign plans and the client gets the 4 tabs', async ({
    page,
  }) => {
    const email = uniqueEmail('e2e.asignacion');
    await registerAndOnboard(page, email, 'Asignable');

    await switchUser(page, DEMO.trainer);
    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow(page, email).click();
    await chooseOption(page, 'select-training-plan', 'Quema grasa 3 días');
    await byTestId(page, 'assign-training-button').click();
    await acceptAlert(page, 'Asignar');
    await expect(page).toHaveURL(/\/app\/assignments$/);
    await expect(pendingRow(page, email)).toHaveCount(0);

    await switchUser(page, DEMO.nutritionist);
    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow(page, email).click();
    await chooseOption(page, 'select-nutrition-plan', 'Déficit moderado alto en proteínas');
    await byTestId(page, 'assign-nutrition-button').click();
    await acceptAlert(page, 'Asignar');
    await expect(page).toHaveURL(/\/app\/assignments$/);

    await switchUser(page, email, 'Str0ng#Pass');
    await expect(page).toHaveURL(/\/app\/training$/);
    await expect(page.locator('ion-tab-button')).toHaveCount(4);
    await expect(byTestId(page, 'plan-name')).toHaveText('Quema grasa 3 días');
  });

  test('reassigning asks to replace the current plan (regression #9)', async ({ page }) => {
    const email = uniqueEmail('e2e.reemplazo');
    await registerAndOnboard(page, email);
    await switchUser(page, DEMO.trainer);
    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow(page, email).click();
    await chooseOption(page, 'select-training-plan', 'Iniciación full body');
    await byTestId(page, 'assign-training-button').click();
    await acceptAlert(page, 'Asignar');
    await expect(page).toHaveURL(/\/app\/assignments$/);

    // Back to the client file from the users list: the plan is already set.
    await byTestId(page, 'tab-users').click();
    await search(page, 'open-adherence', email);
    const card = page
      .locator('[data-testid^="user-card-"]')
      .filter({ visible: true, hasText: email });
    await expect(card).toHaveCount(1);
    await expect(page.locator('[data-testid^="user-card-"]').filter({ visible: true })).toHaveCount(
      1,
    );
    await card.getByTestId('action-assign').click();
    await expect(byTestId(page, 'assign-training')).toContainText('Iniciación full body');
    await chooseOption(page, 'select-training-plan', 'Hipertrofia 4 días');
    await byTestId(page, 'assign-training-button').click();
    await expect(page.locator('ion-alert')).toContainText(
      'El usuario ya tiene el plan «Iniciación full body». ¿Reemplazarlo?',
    );
    await acceptAlert(page, 'Reemplazar');
    await expect(page.locator('ion-toast')).toContainText('Plan asignado');
  });

  test('"create new plan" from an assignment returns with the plan preselected', async ({
    page,
  }) => {
    const email = uniqueEmail('e2e.nuevoplan');
    await registerAndOnboard(page, email);
    await switchUser(page, DEMO.nutritionist);
    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow(page, email).click();
    await byTestId(page, 'create-nutrition-plan').click();

    const name = `Plan E2E ${Date.now()}`;
    await fill(page, 'field-name', name);
    await chooseOption(page, 'field-category', 'Mantenimiento');
    await chooseOption(page, 'field-dietLabel', 'Dieta equilibrada');
    await fill(page, 'field-calories', '2000');
    await fill(page, 'field-proteinsG', '120');
    await fill(page, 'field-carbsG', '250');
    await fill(page, 'field-fatsG', '58');
    await expect(byTestId(page, 'computed-kcal')).toHaveAttribute('data-mismatch', 'false');
    await byTestId(page, 'form-save').click();

    await expect(page).toHaveURL(/\/app\/assignments\/\d+\?mealPlan=\d+$/);
    await expect(byTestId(page, 'select-nutrition-plan')).toContainText(name);
  });

  test('E2E 5 · admin creates, edits and deletes a user', async ({ page }) => {
    const email = uniqueEmail('e2e.admin');
    await login(page, DEMO.admin);
    await byTestId(page, 'tab-users').click();
    await clickOne(page, 'fab-add');

    await fill(page, 'field-firstName', 'Gestionado');
    await fill(page, 'field-lastName', 'Por Admin');
    await fill(page, 'field-email', email);
    await fill(page, 'field-password', 'Str0ng#Pass');
    await chooseOption(page, 'field-gender', 'Otro');
    await chooseOption(page, 'field-role', 'Cliente');
    await fill(page, 'field-birthDate', '01021990');
    await byTestId(page, 'form-save').click();
    await expect(byTestId(page, 'user-name')).toHaveText('Gestionado Por Admin');

    // Regression #2: the edit is saved and shown at once.
    await byTestId(page, 'detail-edit').click();
    await fill(page, 'field-firstName', 'Editado');
    await byTestId(page, 'form-save').click();
    await expect(byTestId(page, 'user-name')).toHaveText('Editado Por Admin');

    await byTestId(page, 'tab-users').click();
    await search(page, 'open-adherence', email);
    const card = page
      .locator('[data-testid^="user-card-"]')
      .filter({ visible: true, hasText: email });
    await expect(card).toHaveCount(1);
    await card.getByTestId('action-delete').click();
    await acceptAlert(page, 'Eliminar');
    await expect(card).toHaveCount(0);
  });

  test('E2E 6 · trainers do not see user edit or delete buttons', async ({ page }) => {
    await login(page, DEMO.trainer);
    await byTestId(page, 'tab-users').click();
    const cards = page.locator('[data-testid^="user-card-"]').filter({ visible: true });
    await expect(cards.first()).toBeVisible();

    await expect(cards.first().getByTestId('action-view')).toBeVisible();
    await expect(page.getByTestId('action-edit').filter({ visible: true })).toHaveCount(0);
    await expect(page.getByTestId('action-delete').filter({ visible: true })).toHaveCount(0);
    await expect(page.getByTestId('fab-add').filter({ visible: true })).toHaveCount(0);
    await page.goto('/app/users/new');
    await expect(page).toHaveURL(/\/app\/catalog$/);
  });

  test('trainer creates an exercise and a workout that uses it', async ({ page }) => {
    const exerciseName = `Ejercicio E2E ${Date.now()}`;
    await login(page, DEMO.trainer);
    await byTestId(page, 'catalog-tab-exercises').click();
    await clickOne(page, 'fab-add');
    await fill(page, 'field-name', exerciseName);
    await byTestId(page, 'option-muscleGroupIds-1').click();
    await byTestId(page, 'add-step').click();
    await fill(page, 'field-steps.0.text', 'Colócate en posición');
    await byTestId(page, 'form-save').click();
    await expect(byTestId(page, 'exercise-detail')).toContainText(exerciseName);
    await expect(byTestId(page, 'exercise-detail')).toContainText('Colócate en posición');

    await byTestId(page, 'tab-catalog').click();
    await byTestId(page, 'catalog-tab-workouts').click();
    await clickOne(page, 'fab-add');
    await fill(page, 'field-name', `Entreno E2E ${Date.now()}`);
    await byTestId(page, 'form-save').click();
    await expect(
      page.getByText('Añade al menos un ejercicio.').filter({ visible: true }),
    ).toBeVisible();

    await byTestId(page, 'add-exercise-row').click();
    await chooseOption(page, 'field-exercises.0.exerciseId', exerciseName);
    await byTestId(page, 'form-save').click();
    await expect(byTestId(page, 'workout-detail')).toContainText(exerciseName);
    await expect(byTestId(page, 'workout-detail')).toContainText('3 × 10');
  });

  test('admin statistics show KPIs and charts per year', async ({ page }) => {
    await login(page, DEMO.admin);
    await byTestId(page, 'tab-statistics').click();
    await expect(byTestId(page, 'kpi-clients')).toBeVisible();
    await expect(byTestId(page, 'popularity-chart')).toBeVisible();
    await expect(byTestId(page, 'growth-chart')).toBeVisible();

    const lastYear = String(new Date().getFullYear() - 1);
    await chooseOption(page, 'year-select', lastYear);
    // The title of the card (the chart repeats it as the caption of its accessible table).
    await expect(
      page.getByRole('heading', { name: `Crecimiento de la plataforma en ${lastYear}` }),
    ).toBeVisible();
  });
});
