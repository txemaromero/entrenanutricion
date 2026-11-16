import { expect, test, type APIRequestContext, type Page } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, fill, login, search, switchUser } from './helpers';

const headersFor = async (request: APIRequestContext, email: string) => {
  const session = await request.post('/api/v1/auth/login', {
    data: { email, password: DEMO_PASSWORD },
  });
  return { Authorization: `Bearer ${((await session.json()) as { access: string }).access}` };
};

/** Pick a food in the open picker and confirm the grams. */
const pickFood = async (page: Page, search: string, grams: string, button = 'portion-save') => {
  const picker = page.getByTestId('food-picker');
  await picker.getByTestId('food-picker-search').locator('input').fill(search);
  await picker.locator('[data-testid^="pick-food-"]').filter({ hasText: search }).first().click();
  await expect(picker.getByTestId('picked-food')).toHaveText(new RegExp(search));
  await picker.getByTestId('portion-grams').locator('input').fill(grams);
  await expect(picker.getByTestId('portion-preview')).toContainText('kcal');
  await picker.getByTestId(button).click();
};

test('the nutritionist composes the sample menu of a plan', async ({ page }) => {
  await login(page, DEMO.nutritionist);
  await page.getByTestId('action-view').filter({ visible: true }).first().click();
  await expect(byTestId(page, 'meal-plan-detail')).toBeVisible();
  const planId = Number(/\/meal-plans\/(\d+)$/.exec(page.url())![1]);
  const headers = await headersFor(page.request, DEMO.nutritionist);
  const original = (await (
    await page.request.get(`/api/v1/meal-plans/${planId}/menu`, { headers })
  ).json()) as { meals: { meal: string; items: { food: { id: number }; grams: number }[] }[] };

  try {
    await byTestId(page, 'edit-menu').click();
    await expect(byTestId(page, 'menu-editor')).toBeVisible();
    const before = await byTestId(page, 'menu-day-totals').innerText();
    await byTestId(page, 'menu-add-snacks').click();
    await pickFood(page, 'Nueces', '30');
    const snacks = byTestId(page, 'menu-edit-snacks');
    await expect(snacks).toContainText('Nueces');
    await expect(byTestId(page, 'menu-day-totals')).not.toHaveText(before);
    await byTestId(page, 'form-save').click();

    await expect(page.getByText('Menú guardado')).toBeVisible();
    await expect(byTestId(page, 'meal-plan-detail')).toBeVisible();
    await expect(byTestId(page, 'menu-meal-snacks')).toContainText('Nueces');
  } finally {
    await page.request.put(`/api/v1/meal-plans/${planId}/menu`, {
      headers,
      data: {
        items: original.meals.flatMap((meal) =>
          meal.items.map((item) => ({ meal: meal.meal, food_id: item.food.id, grams: item.grams })),
        ),
      },
    });
  }
});

test('the client logs meals in the diary and uses the shopping list', async ({ page }) => {
  await login(page, DEMO.activeClient);
  const headers = await headersFor(page.request, DEMO.activeClient);
  const today = new Date();
  const iso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(
    today.getDate(),
  ).padStart(2, '0')}`;
  const clearToday = async () => {
    const day = (await (
      await page.request.get('/api/v1/me/food-log', { headers, params: { date: iso } })
    ).json()) as { meals: { entries: { id: number }[] }[] };
    for (const entry of day.meals.flatMap((meal) => meal.entries)) {
      await page.request.delete(`/api/v1/me/food-log/${entry.id}`, { headers });
    }
  };
  await clearToday();

  try {
    await byTestId(page, 'tab-nutrition').click();
    await expect(byTestId(page, 'menu-view')).toBeVisible();
    await byTestId(page, 'open-food-diary').click();
    await expect(byTestId(page, 'diary-date-label')).toHaveText('Hoy');

    // Add a food, change its grams and delete it.
    await byTestId(page, 'diary-add-breakfast').click();
    await pickFood(page, 'Plátano', '120');
    await expect(page.getByText('Anotado en el diario')).toBeVisible();
    const breakfast = byTestId(page, 'diary-meal-breakfast');
    await expect(breakfast).toContainText('Plátano');
    await expect(breakfast).toContainText('120 g');
    await breakfast.locator('[data-testid^="diary-edit-"]').first().click();
    await fill(page, 'portion-grams', '60');
    await page.getByTestId('food-picker').getByTestId('portion-save').click();
    await expect(breakfast).toContainText('60 g');
    await breakfast.locator('[data-testid^="diary-remove-"]').first().click();
    await expect(breakfast.locator('[data-testid^="diary-entry-"]')).toHaveCount(0);

    // Copy the lunch of the sample menu.
    await byTestId(page, 'diary-copy-lunch').click();
    await expect(
      byTestId(page, 'diary-meal-lunch').locator('[data-testid^="diary-entry-"]').first(),
    ).toBeVisible();
    await expect(byTestId(page, 'diary-totals')).not.toContainText(/^Consumido\s*0 \//);
    await expect(byTestId(page, 'diary-summary')).toContainText('días anotados');

    // Shopping list: ticks stay on the device.
    await page.goto('/app/nutrition/shopping-list');
    const pending = byTestId(page, 'shopping-pending');
    await expect(pending).toContainText(/Te faltan \d+ productos/);
    const total = Number(/(\d+)/.exec(await pending.innerText())![1]);
    await page.locator('[data-testid^="shopping-item-"] ion-checkbox').first().click();
    await expect(pending).toContainText(`${total - 1}`);
    await page.reload();
    await expect(byTestId(page, 'shopping-pending')).toContainText(`${total - 1}`);
    await byTestId(page, 'shopping-days-3').click();
    await expect(byTestId(page, 'shopping-pending')).toContainText(`${total - 1}`);
    await page.getByRole('button', { name: 'Desmarcar todo' }).click();
    await expect(byTestId(page, 'shopping-pending')).toContainText(`${total}`);
  } finally {
    await clearToday();
  }
});

test('the staff sees the last week of the client diary', async ({ page }) => {
  await login(page, DEMO.nutritionist);
  await switchUser(page, DEMO.trainer);
  await byTestId(page, 'tab-users').click();
  await search(page, 'open-adherence', 'Lucía');
  await page
    .locator('[data-testid^="user-card-"]')
    .filter({ visible: true, hasText: 'Lucía Fernández' })
    .getByTestId('action-view')
    .click();
  const summary = byTestId(page, 'diary-summary');
  await expect(summary).toContainText('Diario de comidas (7 días)');
  await expect(summary).toContainText(/días? anotados? de 7/);
  await expect(summary.getByTestId('diary-summary-day')).toHaveCount(7);
});
