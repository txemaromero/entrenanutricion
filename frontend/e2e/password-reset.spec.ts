import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import { byTestId, fill, login } from './helpers';

const BACKEND_DIR = path.resolve(process.cwd(), '..', 'backend');
const PYTHON = process.env.E2E_PYTHON ?? 'python';
const NEW_PASSWORD = 'N3w#Password';

/** Reset link for `email`, built like the emailed one (in development the email goes to the console). */
const resetLink = (email: string): string => {
  const code = [
    'from django.contrib.auth.tokens import default_token_generator as tokens',
    'from django.utils.encoding import force_bytes',
    'from django.utils.http import urlsafe_base64_encode',
    'from apps.accounts.models import User',
    `user = User.objects.get(email__iexact=${JSON.stringify(email)})`,
    'uid = urlsafe_base64_encode(force_bytes(user.pk))',
    'print(f"LINK=/reset-password?uid={uid}&token={tokens.make_token(user)}")',
  ].join('\n');
  const python =
    PYTHON.includes('\\') || PYTHON.includes('/') ? path.resolve(BACKEND_DIR, PYTHON) : PYTHON;
  const output = execFileSync(python, ['manage.py', 'shell', '-c', code], {
    cwd: BACKEND_DIR,
    encoding: 'utf8',
  });
  const link = /LINK=(\S+)/.exec(output)?.[1];
  if (!link) throw new Error(`No reset link in: ${output}`);
  return link;
};

/** A fresh account, so the demo users keep their password. */
const newAccount = async (page: Page): Promise<string> => {
  const email = `reset-${Date.now()}@example.com`;
  const response = await page.request.post('/api/v1/auth/register', {
    data: {
      first_name: 'Laura',
      last_name: 'Reset',
      email,
      password: 'Str0ng#Pass',
      birth_date: '1992-04-12',
      gender: 'F',
      terms_accepted: true,
      health_data_consent: true,
    },
  });
  expect(response.status()).toBe(201);
  return email;
};

test('a user resets a forgotten password with the emailed link', async ({ page }) => {
  const email = await newAccount(page);

  await page.goto('/login');
  await byTestId(page, 'forgot-password-link').click();
  await expect(page).toHaveURL(/\/forgot-password$/);
  // Both pages share the email field id: wait until the login page has slid away.
  await expect(byTestId(page, 'login-submit')).toHaveCount(0);
  await fill(page, 'field-email', email);
  await byTestId(page, 'forgot-submit').click();
  await expect(byTestId(page, 'forgot-sent')).toContainText(email);

  await page.goto(resetLink(email));
  await fill(page, 'field-newPassword', NEW_PASSWORD);
  await fill(page, 'field-confirmPassword', NEW_PASSWORD);
  await byTestId(page, 'reset-submit').click();

  await expect(page).toHaveURL(/\/login\?passwordReset=1$/);
  await expect(byTestId(page, 'password-reset-done')).toBeVisible();
  await login(page, email, NEW_PASSWORD);
  await expect(page).toHaveURL(/\/onboarding$/);
});

test('a used or incomplete link asks for a new one', async ({ page }) => {
  const email = await newAccount(page);
  const link = resetLink(email);
  const [, query] = link.split('?');
  const params = Object.fromEntries(new URLSearchParams(query));
  const used = await page.request.post('/api/v1/auth/password-reset/confirm', {
    data: { ...params, new_password: NEW_PASSWORD, confirm_password: NEW_PASSWORD },
  });
  expect(used.status()).toBe(204);

  await page.goto(link);
  await fill(page, 'field-newPassword', 'Other#Pass9');
  await fill(page, 'field-confirmPassword', 'Other#Pass9');
  await byTestId(page, 'reset-submit').click();
  await expect(byTestId(page, 'reset-invalid')).toBeVisible();

  await page.goto('/reset-password');
  await expect(byTestId(page, 'reset-invalid')).toBeVisible();
});
