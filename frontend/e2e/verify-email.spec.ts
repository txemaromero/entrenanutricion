import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '@playwright/test';

import { byTestId, login } from './helpers';

const BACKEND_DIR = path.resolve(process.cwd(), '..', 'backend');
const PYTHON = process.env.E2E_PYTHON ?? 'python';
const PASSWORD = 'Str0ng#Pass';

/** Verification link for `email`, built like the emailed one (in development it goes to the console). */
const verificationLink = (email: string): string => {
  const code = [
    'from apps.accounts.models import User',
    'from apps.accounts.services import email_verification_token',
    `user = User.objects.get(email__iexact=${JSON.stringify(email)})`,
    'print(f"LINK=/verify-email?token={email_verification_token(user)}")',
  ].join('\n');
  const python =
    PYTHON.includes('\\') || PYTHON.includes('/') ? path.resolve(BACKEND_DIR, PYTHON) : PYTHON;
  const output = execFileSync(python, ['manage.py', 'shell', '-c', code], {
    cwd: BACKEND_DIR,
    encoding: 'utf8',
  });
  const link = /LINK=(\S+)/.exec(output)?.[1];
  if (!link) throw new Error(`No verification link in: ${output}`);
  return link;
};

test('a new account confirms its email with the link', async ({ page }) => {
  const email = `verify-${Date.now()}@example.com`;
  const response = await page.request.post('/api/v1/auth/register', {
    data: {
      first_name: 'Nora',
      last_name: 'Prueba',
      email,
      password: PASSWORD,
      birth_date: '1994-02-10',
      gender: 'F',
      terms_accepted: true,
      health_data_consent: true,
    },
  });
  expect(response.status()).toBe(201);

  await login(page, email, PASSWORD);
  const banner = byTestId(page, 'verify-email-banner');
  await expect(banner).toContainText(`te hemos enviado un enlace a ${email}`);
  await byTestId(page, 'resend-verification').click();
  await expect(page.getByText('Te hemos enviado un enlace nuevo')).toBeVisible();

  await page.goto('/verify-email?token=not-a-token');
  await expect(byTestId(page, 'verify-failed')).toContainText(
    'El enlace de confirmación no es válido.',
  );

  await page.goto(verificationLink(email));
  await expect(byTestId(page, 'email-verified')).toHaveText('¡Correo confirmado!');
  await byTestId(page, 'verify-continue').click();
  await expect(page).toHaveURL(/\/onboarding$/);
  await expect(page.getByTestId('verify-email-banner')).toHaveCount(0);
});
