import { expect, test } from '@playwright/test';

import { DEMO, byTestId, clickOne, login, search } from './helpers';

test('the staff sees who needs help first and the weeks of one client', async ({ page }) => {
  await login(page, DEMO.trainer);
  await byTestId(page, 'tab-users').click();
  await clickOne(page, 'open-adherence');
  await expect(page).toHaveURL(/\/app\/users\/adherence$/);

  const cards = page.locator('[data-testid^="adherence-"][data-status]').filter({ visible: true });
  await expect(cards.first()).toBeVisible();
  // The demo has clients who stopped training: they come first.
  await expect(cards.first()).toHaveAttribute('data-status', 'inactive');
  await expect(byTestId(page, 'adherence-filter-inactive')).toContainText(/Inactivo \(\d+\)/);

  await byTestId(page, 'adherence-filter-on_track').click();
  await expect(cards.first()).toHaveAttribute('data-status', 'on_track');
  const statuses = await cards.evaluateAll((elements) =>
    elements.map((element) => element.getAttribute('data-status')),
  );
  expect(new Set(statuses)).toEqual(new Set(['on_track']));

  // The demo client trains regularly; their profile shows the last four weeks.
  await search(page, 'adherence-filter', 'Lucía');
  const lucia = cards.filter({ hasText: 'Lucía Fernández' });
  await expect(lucia).toHaveCount(1);
  await expect(lucia).toContainText('% de adherencia');
  await lucia.click();
  await expect(byTestId(page, 'user-detail')).toBeVisible();
  await expect(byTestId(page, 'client-adherence')).toContainText('Adherencia al plan');
  // The four weeks are a chart; its values are also a table for screen readers.
  await expect(byTestId(page, 'adherence-weeks')).toBeVisible();
  await expect(byTestId(page, 'client-adherence').getByTestId('adherence-week')).toHaveCount(4);
});
