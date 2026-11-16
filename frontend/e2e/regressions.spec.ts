import { expect, test, type Page } from '@playwright/test';

import { DEMO, byTestId, login, switchUser } from './helpers';

const visibleContent = (page: Page) => page.locator('ion-content').filter({ visible: true }).last();

const scrollTop = (page: Page) =>
  visibleContent(page).evaluate(async (element) => {
    const scroller = await (element as HTMLIonContentElement).getScrollElement();
    return scroller.scrollTop;
  });

/** Raw i18n keys ("enums.goal.x") or backend identifiers ("training_plan") on screen. */
const untranslated = async (page: Page) => {
  const text = await visibleContent(page).innerText();
  const keys = text.match(
    /\b(app|common|tabs|auth|errors|enums|training|exercise|nutrition|progress|profile|staff|catalog|mealPlans|users|assignments|statistics|onboarding|planStatus|motivation)\.[a-zA-Z_]+/g,
  );
  const identifiers = text.match(/\b[a-z]+_[a-z_]+\b/g);
  return [...(keys ?? []), ...(identifiers ?? [])];
};

test('regression #8 · the exercise detail always opens at the top', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await page
    .locator('[data-testid^="plan-workout-"][data-status="available"]')
    .filter({ visible: true })
    .click();
  await byTestId(page, 'open-exercise-1').click();
  await expect(byTestId(page, 'big-circles')).toBeVisible();

  await visibleContent(page).evaluate((element) =>
    (element as HTMLIonContentElement).scrollToBottom(0),
  );
  await expect.poll(() => scrollTop(page)).toBeGreaterThan(0);

  await page.goBack();
  await byTestId(page, 'open-exercise-2').click();
  await expect(byTestId(page, 'big-circles')).toBeVisible();
  await expect.poll(() => scrollTop(page)).toBe(0);
});

test('regression #3 · no screen shows raw keys or variable names', async ({ page }) => {
  const visit = async (testId: string) => {
    await byTestId(page, testId).click();
    await expect(visibleContent(page)).not.toContainText('Cargando');
    await page.waitForLoadState('networkidle');
    expect(await untranslated(page), testId).toEqual([]);
  };

  await login(page, DEMO.activeClient);
  for (const tab of ['tab-training', 'tab-nutrition', 'tab-progress', 'tab-profile'])
    await visit(tab);

  await switchUser(page, DEMO.admin);
  for (const tab of [
    'tab-catalog',
    'tab-mealPlans',
    'tab-users',
    'tab-assignments',
    'tab-statistics',
  ]) {
    await visit(tab);
  }
});
