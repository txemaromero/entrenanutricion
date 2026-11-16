import { expect, test } from '@playwright/test';

import { DEMO, acceptAlert, byTestId, chooseOption, fill, login, clickOne } from './helpers';

test('the nutritionist creates, edits and deletes a food of the library', async ({ page }) => {
  const name = `Kéfir ${Date.now()}`;
  await login(page, DEMO.nutritionist);
  await byTestId(page, 'open-food-library').click();
  await expect(page).toHaveURL(/\/app\/meal-plans\/foods$/);
  // Both pages have an add button while the plans page slides away.
  await expect(byTestId(page, 'open-food-library')).toHaveCount(0);
  await clickOne(page, 'fab-add');
  await expect(page).toHaveURL(/\/foods\/new$/);

  await fill(page, 'field-name', name);
  await chooseOption(page, 'field-category', 'Lácteos');
  await fill(page, 'field-calories', '64');
  await fill(page, 'field-proteinsG', '3.3');
  await fill(page, 'field-carbsG', '4.5');
  await fill(page, 'field-fatsG', '3.5');
  await fill(page, 'field-sugarsG', '6');
  await byTestId(page, 'form-save').click();
  await expect(
    page.getByText('Los azúcares no pueden superar los carbohidratos.').filter({ visible: true }),
  ).toBeVisible();

  await fill(page, 'field-sugarsG', '4');
  await fill(page, 'field-calciumMg', '120');
  await byTestId(page, 'form-save').click();
  await expect(page).toHaveURL(/\/foods\/\d+$/);
  await expect(byTestId(page, 'food-detail')).toContainText(name);
  await expect(byTestId(page, 'food-kcal')).toHaveText('64 kcal por 100 g');
  await expect(byTestId(page, 'food-micronutrients')).toContainText('Calcio');
  await expect(byTestId(page, 'food-micronutrients')).toContainText('120 mg');

  // An emptied field is cleared on save.
  await byTestId(page, 'detail-edit').click();
  await fill(page, 'field-calciumMg', '');
  await fill(page, 'field-potassiumMg', '150');
  await byTestId(page, 'form-save').click();
  await expect(byTestId(page, 'food-micronutrients')).toContainText('Potasio');
  await expect(byTestId(page, 'food-micronutrients')).not.toContainText('Calcio');

  await byTestId(page, 'tab-mealPlans').click();
  await byTestId(page, 'open-food-library').click();
  await fill(page, 'food-search', name);
  const card = page.locator('[data-testid^="food-card-"]').filter({ visible: true, hasText: name });
  await expect(card).toHaveCount(1);
  await card.getByTestId('action-delete').click();
  await acceptAlert(page, 'Eliminar');
  await expect(card).toHaveCount(0);
});

test('clients browse the food library from their nutrition page', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await byTestId(page, 'tab-nutrition').click();
  await byTestId(page, 'open-food-library').click();
  await expect(page).toHaveURL(/\/app\/nutrition\/foods$/);
  await expect(page.getByTestId('fab-add').filter({ visible: true })).toHaveCount(0);

  await chooseOption(page, 'food-category', 'Frutos secos y semillas');
  const cards = page.locator('[data-testid^="food-card-"]').filter({ visible: true });
  await expect(cards.filter({ hasText: 'Almendras' })).toHaveCount(1);
  await expect(cards.filter({ hasText: 'Plátano' })).toHaveCount(0);
  await expect(cards.getByTestId('action-edit')).toHaveCount(0);

  await cards.filter({ hasText: 'Almendras' }).getByTestId('action-view').click();
  await expect(page).toHaveURL(/\/app\/nutrition\/foods\/\d+$/);
  await expect(byTestId(page, 'food-detail')).toContainText('Almendras');
  await expect(byTestId(page, 'food-micronutrients')).toContainText('Magnesio');
  await expect(page.getByTestId('detail-edit').filter({ visible: true })).toHaveCount(0);
});
