import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

import { DEMO, byTestId, clickOne, login, search, switchUser } from './helpers';

/** WCAG 2.1 A/AA audit of the visible page; hidden Ionic pages kept in the DOM are excluded. */
const audit = async (page: Page, name: string) => {
  await page.waitForLoadState('networkidle');
  // Tab switches are in-app navigations, so the load state above is already reached. Wait for the
  // visible page to finish loading and for the tap ripple (a translucent overlay that axe would
  // take as the label background) to fade out.
  await expect(page.locator('.ion-page:not(.ion-page-hidden) [aria-busy="true"]')).toHaveCount(0);
  await expect(page.locator('ion-ripple-effect .ripple-effect')).toHaveCount(0);
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .exclude('.ion-page-hidden')
    .analyze();
  const serious = results.violations
    .filter((violation) => violation.impact === 'critical' || violation.impact === 'serious')
    .map(
      (violation) =>
        `${name}: ${violation.id} ${violation.help} → ${violation.nodes
          .slice(0, 3)
          .map((node) => `${node.target.join(' ')} (${node.failureSummary ?? ''})`)
          .join(' | ')}`,
    );
  return serious;
};

/** Opens each tab and audits it; the tab bar is part of every audit. */
const auditTabs = async (page: Page, tabs: string[]) => {
  const problems: string[] = [];
  for (const tab of tabs) {
    await byTestId(page, tab).click();
    problems.push(...(await audit(page, tab)));
  }
  return problems;
};

test.describe('accessibility (WCAG 2.1 A/AA, critical and serious)', () => {
  test('public screens', async ({ page }) => {
    const problems: string[] = [];
    for (const path of [
      '/welcome',
      '/login',
      '/register',
      '/forgot-password',
      '/reset-password',
      '/privacy',
      '/verify-email?token=invalid',
    ]) {
      await page.goto(path);
      problems.push(...(await audit(page, path)));
    }
    expect(problems).toEqual([]);
  });

  test('active client screens', async ({ page }) => {
    await login(page, DEMO.activeClient);
    const problems = await auditTabs(page, [
      'tab-training',
      'tab-nutrition',
      'tab-progress',
      'tab-profile',
    ]);
    expect(problems).toEqual([]);
  });

  test('client screens of the future lines (badges and food library)', async ({ page }) => {
    await login(page, DEMO.activeClient);
    const problems: string[] = [];
    await byTestId(page, 'tab-progress').click();
    await byTestId(page, 'badges-view').click();
    await expect(page).toHaveURL(/\/app\/progress\/badges$/);
    problems.push(...(await audit(page, 'badges')));
    await byTestId(page, 'tab-nutrition').click();
    await byTestId(page, 'open-food-library').click();
    await expect(page).toHaveURL(/\/app\/nutrition\/foods$/);
    problems.push(...(await audit(page, 'foods')));
    expect(problems).toEqual([]);
  });

  test('sets, records, notes and adherence (phase 12)', async ({ page }) => {
    await login(page, DEMO.activeClient);
    const problems: string[] = [];
    await page
      .locator('[data-testid^="plan-workout-"][data-status="available"]')
      .filter({ visible: true })
      .click();
    await byTestId(page, 'sets-toggle-1').click();
    await expect(byTestId(page, 'sets-form-1')).toBeVisible();
    problems.push(...(await audit(page, 'sets editor')));
    await byTestId(page, 'open-exercise-1').click();
    await expect(byTestId(page, 'exercise-progress')).toBeVisible();
    problems.push(...(await audit(page, 'exercise progress')));
    await byTestId(page, 'tab-progress').click();
    await byTestId(page, 'segment-workout').click();
    await expect(byTestId(page, 'records-card')).toBeVisible();
    problems.push(...(await audit(page, 'records')));
    await byTestId(page, 'tab-profile').click();
    await byTestId(page, 'notes-entry').click();
    await expect(page).toHaveURL(/\/app\/profile\/notes$/);
    problems.push(...(await audit(page, 'notes')));

    await switchUser(page, DEMO.trainer);
    await byTestId(page, 'tab-users').click();
    await clickOne(page, 'open-adherence');
    await expect(page.locator('[data-testid^="adherence-"][data-status]').first()).toBeVisible();
    problems.push(...(await audit(page, 'adherence')));
    await search(page, 'adherence-filter', 'Lucía');
    await page
      .locator('[data-testid^="adherence-"][data-status]')
      .filter({ visible: true, hasText: 'Lucía Fernández' })
      .click();
    await expect(byTestId(page, 'client-adherence')).toBeVisible();
    problems.push(...(await audit(page, 'client adherence')));
    expect(problems).toEqual([]);
  });

  test('menus, food diary and shopping list (phase 13)', async ({ page }) => {
    await login(page, DEMO.activeClient);
    const problems: string[] = [];
    await byTestId(page, 'tab-nutrition').click();
    await expect(byTestId(page, 'menu-view')).toBeVisible();
    problems.push(...(await audit(page, 'nutrition with menu')));
    await byTestId(page, 'open-food-diary').click();
    await expect(byTestId(page, 'diary-totals')).toBeVisible();
    problems.push(...(await audit(page, 'food diary')));
    await byTestId(page, 'diary-add-breakfast').click();
    await expect(page.getByTestId('food-picker-search')).toBeVisible();
    problems.push(...(await audit(page, 'food picker')));
    await page.getByTestId('food-picker-close').click();
    await page.goto('/app/nutrition/shopping-list');
    await expect(byTestId(page, 'shopping-pending')).toBeVisible();
    problems.push(...(await audit(page, 'shopping list')));

    await switchUser(page, DEMO.nutritionist);
    await page.getByTestId('action-view').filter({ visible: true }).first().click();
    await byTestId(page, 'edit-menu').click();
    await expect(byTestId(page, 'menu-editor')).toBeVisible();
    problems.push(...(await audit(page, 'menu editor')));
    expect(problems).toEqual([]);
  });

  test('admin screens', async ({ page }) => {
    await login(page, DEMO.admin);
    const problems = await auditTabs(page, [
      'tab-catalog',
      'tab-mealPlans',
      'tab-users',
      'tab-assignments',
      'tab-statistics',
    ]);
    expect(problems).toEqual([]);
  });
});
