import { expect, test } from '@playwright/test';

import { DEMO, byTestId, login } from './helpers';

declare global {
  interface Window {
    cspViolations: string[];
  }
}

/**
 * Runs against the production build with its headers (`vite preview`, nginx or Render):
 * E2E_BASE_URL=http://127.0.0.1:4173. The dev server sends no CSP, so the test is skipped there.
 */
test('the production build works under its Content-Security-Policy', async ({ page }) => {
  await page.addInitScript(() => {
    window.cspViolations = [];
    document.addEventListener('securitypolicyviolation', (event) =>
      window.cspViolations.push(
        `${event.violatedDirective} ${event.blockedURI} ${event.sourceFile}:${event.lineNumber}:${event.columnNumber}`,
      ),
    );
  });
  const response = await page.goto('/welcome');
  test.skip(!response?.headers()['content-security-policy'], 'served without a CSP (dev server)');

  await login(page, DEMO.activeClient);
  await expect(byTestId(page, 'plan-name')).toBeVisible();
  for (const tab of ['tab-nutrition', 'tab-progress', 'tab-profile', 'tab-training']) {
    await byTestId(page, tab).click();
  }
  await page
    .locator('[data-testid^="plan-workout-"][data-status="available"]')
    .filter({ visible: true })
    .click();
  await expect(page).toHaveURL(/\/workouts\/\d+$/);
  // Charts (canvas), images of the exercises and the session refresh after a reload.
  await page.reload();
  await expect(page).toHaveURL(/\/workouts\/\d+$/);
  await byTestId(page, 'tab-progress').click();
  await byTestId(page, 'segment-weight').click();

  const violations = await page.evaluate(() => window.cspViolations);
  expect(violations).toEqual([]);
});
