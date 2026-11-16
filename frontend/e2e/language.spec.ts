import { expect, test } from '@playwright/test';

import { byTestId } from './helpers';

test('the language changes live and is remembered', async ({ page }) => {
  await page.goto('/welcome');
  await expect(page.getByRole('heading', { name: 'Bienvenido a entrenanutricion' })).toBeVisible();

  await byTestId(page, 'language-menu').click();
  await page.getByTestId('language-option-en').click();

  await expect(page.getByRole('heading', { name: 'Welcome to entrenanutricion' })).toBeVisible();
  await expect(byTestId(page, 'welcome-register')).toHaveText('Sign up');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');

  await page.reload();
  await expect(page.getByRole('heading', { name: 'Welcome to entrenanutricion' })).toBeVisible();

  await byTestId(page, 'language-menu').click();
  await page.getByTestId('language-option-ca').click();
  await expect(byTestId(page, 'welcome-login')).toHaveText('Iniciar sessió');
});
