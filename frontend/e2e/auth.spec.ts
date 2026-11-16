import { expect, test } from '@playwright/test';

import { DEMO, byTestId, chooseOption, fill, login, selectedTabs, uniqueEmail } from './helpers';

test.describe('authentication', () => {
  test('wrong credentials show a specific message', async ({ page }) => {
    await page.goto('/login');
    await fill(page, 'field-email', DEMO.admin);
    await fill(page, 'field-password', 'Wrong#Pass1');
    await byTestId(page, 'login-submit').click();

    await expect(byTestId(page, 'login-error')).toHaveText(
      'El email o la contraseña no son correctos.',
    );
  });

  test('a password that looks like the name is refused under the field', async ({ page }) => {
    await page.goto('/register');
    await fill(page, 'field-firstName', 'Valentina');
    await fill(page, 'field-lastName', 'Automática');
    await fill(page, 'field-email', uniqueEmail('e2e.parecida'));
    await fill(page, 'field-password', 'Valentina#1');
    await fill(page, 'field-birthDate', '10031995');
    await chooseOption(page, 'field-gender', 'Mujer');
    await byTestId(page, 'field-termsAccepted').click();
    await byTestId(page, 'field-healthDataConsent').click();
    await byTestId(page, 'register-submit').click();

    // The browser checks the rules it knows; this one only the server can (it knows the name).
    await expect(byTestId(page, 'field-password')).toContainText(
      'Se parece demasiado a tu nombre o a tu email.',
    );
    await expect(page).toHaveURL(/\/register$/);
  });

  test('admin logs in, sees five tabs with one active and logs out', async ({ page }) => {
    await login(page, DEMO.admin);

    await expect(page).toHaveURL(/\/app\/catalog$/);
    await expect(page.locator('ion-tab-button')).toHaveCount(5);
    // Regression #10: only the tab of the current route is highlighted.
    await expect(selectedTabs(page)).toHaveCount(1);
    await byTestId(page, 'tab-users').click();
    await expect(page).toHaveURL(/\/app\/users$/);
    await expect(selectedTabs(page)).toHaveCount(1);
    await expect(byTestId(page, 'tab-users')).toHaveClass(/tab-selected/);

    await byTestId(page, 'admin-profile-button').click();
    await expect(page).toHaveURL(/\/app\/profile$/);
    await byTestId(page, 'logout').click();
    await expect(page).toHaveURL(/\/login$/);

    // The session is really gone: protected pages bounce back to login.
    await page.goto('/app/users');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('the session survives a reload when "remember me" is ticked', async ({ page }) => {
    await page.goto('/login');
    await fill(page, 'field-email', DEMO.trainer);
    await fill(page, 'field-password', 'entrenanutricion#2025');
    await byTestId(page, 'field-rememberMe').click();
    await byTestId(page, 'login-submit').click();
    await expect(page).toHaveURL(/\/app\/catalog$/);

    await page.reload();

    await expect(page).toHaveURL(/\/app\/catalog$/);
    await expect(page.locator('ion-tab-button')).toHaveCount(4);
  });

  test('routes of other roles redirect to the home tab', async ({ page }) => {
    await login(page, DEMO.nutritionist);
    await expect(page).toHaveURL(/\/app\/meal-plans$/);

    await page.goto('/app/statistics');

    await expect(page).toHaveURL(/\/app\/meal-plans$/);
  });
});
