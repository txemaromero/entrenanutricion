import { readFileSync } from 'node:fs';

import { expect, test } from '@playwright/test';

import {
  DEMO,
  DEMO_PASSWORD,
  byTestId,
  fill,
  login,
  registerAndOnboard,
  uniqueEmail,
} from './helpers';

test('the privacy policy is public and linked from the registration form', async ({ page }) => {
  await page.goto('/register');
  await page.getByRole('link', { name: 'Leer la política de privacidad' }).click();

  await expect(page).toHaveURL(/\/privacy$/);
  const policy = byTestId(page, 'privacy-policy');
  await expect(policy).toContainText('Responsable del tratamiento');
  await expect(policy).toContainText('art. 9.2.a RGPD');
});

test('a client downloads the data and deletes the account', async ({ page }) => {
  const email = uniqueEmail('e2e.privacy');
  await registerAndOnboard(page, email, 'Privada');
  await byTestId(page, 'tab-profile').click();

  const [download] = await Promise.all([
    page.waitForEvent('download'),
    byTestId(page, 'privacy-export').click(),
  ]);
  expect(download.suggestedFilename()).toMatch(/^entrenanutricion-datos-\d{8}\.json$/);
  const exported = JSON.parse(readFileSync((await download.path())!, 'utf8'));
  expect(exported.account.email).toBe(email);
  expect(exported.onboarding.health).toBeTruthy();

  await byTestId(page, 'privacy-delete').click();
  const modal = page.getByTestId('delete-account-modal');
  await fill(page, 'delete-password', 'Wrong#Pass1');
  await modal.getByTestId('delete-confirm').click();
  await expect(modal.getByRole('alert')).toHaveText('La contraseña actual es incorrecta.');
  await fill(page, 'delete-password', 'Str0ng#Pass');
  await modal.getByTestId('delete-confirm').click();
  await expect(page).toHaveURL(/\/welcome$/);

  const relogin = await page.request.post('/api/v1/auth/login', {
    data: { email, password: 'Str0ng#Pass' },
  });
  expect(relogin.status()).toBe(401);
});

test('users created by an admin accept the policy before using the app', async ({ page }) => {
  const email = uniqueEmail('e2e.consent');
  const session = await page.request.post('/api/v1/auth/login', {
    data: { email: DEMO.admin, password: DEMO_PASSWORD },
  });
  const { access } = (await session.json()) as { access: string };
  const created = await page.request.post('/api/v1/users', {
    headers: { Authorization: `Bearer ${access}` },
    data: {
      first_name: 'Sin',
      last_name: 'Consentimiento',
      email,
      password: 'Str0ng#Pass',
      gender: 'O',
      role: 'client',
      birth_date: '1990-01-01',
    },
  });
  expect(created.status()).toBe(201);
  await page.context().clearCookies();

  await login(page, email, 'Str0ng#Pass');
  const modal = page.getByTestId('consent-modal');
  await expect(modal).toBeVisible();
  await expect(modal.getByTestId('consent-accept')).toHaveAttribute('aria-disabled', 'true');
  await modal.getByTestId('consent-privacy').click();
  await modal.getByTestId('consent-health').click();
  await modal.getByTestId('consent-accept').click();
  await expect(modal).toHaveCount(0);
  await expect(page).toHaveURL(/\/onboarding$/);
});
