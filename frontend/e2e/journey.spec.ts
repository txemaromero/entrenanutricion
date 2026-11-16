import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';

import { expect, test, type Page } from '@playwright/test';

import {
  DEMO,
  acceptAlert,
  byTestId,
  chooseOption,
  fill,
  registerAndOnboard,
  search,
  switchUser,
  searchPending,
  uniqueEmail,
} from './helpers';

declare global {
  interface Window {
    cspViolations: string[];
  }
}

const BACKEND_DIR = path.resolve(process.cwd(), '..', 'backend');
const PYTHON = process.env.E2E_PYTHON ?? 'python';
const PASSWORD = 'Str0ng#Pass';

/** The emailed verification link, built like the real one (in development emails go to the console). */
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
  return /LINK=(\S+)/.exec(output)![1];
};

/** A name only with letters (the registration form does not accept digits). */
const uniqueName = () =>
  'Viaje' + [...String(Date.now()).slice(-6)].map((digit) => 'abcdefghij'[Number(digit)]).join('');

/**
 * Collects what should never happen while using the app: uncaught errors, console errors other
 * than the expected 4xx answers, server errors (5xx) and Content-Security-Policy violations.
 */
const watchProblems = async (page: Page) => {
  const problems: string[] = [];
  page.on('pageerror', (error) => problems.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    const text = message.text();
    if (message.type() !== 'error') return;
    if (/Failed to load resource: the server responded with a status of 4\d\d/.test(text)) return;
    const where = message.location();
    problems.push(`console: ${text.slice(0, 60)} @ ${page.url()} ${where.url}:${where.lineNumber}`);
  });
  page.on('response', (response) => {
    if (response.status() >= 500) problems.push(`${response.status()} ${response.url()}`);
  });
  await page.addInitScript(() => {
    window.cspViolations = [];
    document.addEventListener('securitypolicyviolation', (event) =>
      window.cspViolations.push(`${event.violatedDirective} ${event.blockedURI}`),
    );
  });
  return async () => {
    const violations = await page.evaluate(() => window.cspViolations ?? []);
    return [...problems, ...violations.map((violation) => `csp: ${violation}`)];
  };
};

test('the whole journey of a client, from the registration to the deletion of the account', async ({
  page,
}) => {
  test.setTimeout(300_000);
  const problems = await watchProblems(page);
  const email = uniqueEmail('e2e.journey');
  const name = uniqueName();
  const fullName = `${name} Automática`;
  const pendingRow = () =>
    page
      .locator('[data-testid^="pending-user-"]')
      .filter({ visible: true })
      .filter({ hasText: email });

  await test.step('registration, onboarding and email confirmation', async () => {
    await registerAndOnboard(page, email, name);
    await expect(byTestId(page, 'plan-status-title')).toHaveText('Estamos preparando tu plan…');
    await expect(byTestId(page, 'verify-email-banner')).toContainText(email);

    await page.goto(verificationLink(email));
    await expect(byTestId(page, 'email-verified')).toHaveText('¡Correo confirmado!');
    await byTestId(page, 'verify-continue').click();
    await expect(page).toHaveURL(/\/app\/status$/);
    await expect(page.getByTestId('verify-email-banner')).toHaveCount(0);
  });

  await test.step('the client writes to the team while waiting for the plans', async () => {
    await byTestId(page, 'notes-entry').click();
    await expect(page).toHaveURL(/\/app\/profile\/notes$/);
    await fill(page, 'note-body', '¿Cuándo tendré mi plan?');
    await byTestId(page, 'send-note').click();
    await expect(byTestId(page, 'notes-thread')).toContainText('¿Cuándo tendré mi plan?');
  });

  await test.step('the trainer answers the note and assigns the training plan', async () => {
    await switchUser(page, DEMO.trainer);
    await byTestId(page, 'tab-users').click();
    const inbox = byTestId(page, 'notes-inbox');
    await expect(inbox).toContainText(fullName);
    await inbox.locator('ion-item').filter({ hasText: fullName }).click();
    const thread = byTestId(page, 'notes-thread');
    await expect(thread).toContainText('¿Cuándo tendré mi plan?');
    await expect(thread).toContainText('Nueva');
    await fill(page, 'note-body', 'Ya lo tienes, ¡a entrenar!');
    await byTestId(page, 'send-note').click();
    await expect(thread).toContainText('Ya lo tienes, ¡a entrenar!');

    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow().click();
    await chooseOption(page, 'select-training-plan', 'Quema grasa 3 días');
    await byTestId(page, 'assign-training-button').click();
    await acceptAlert(page, 'Asignar');
    await expect(page).toHaveURL(/\/app\/assignments$/);
  });

  await test.step('the nutritionist assigns the nutrition plan (it has a sample menu)', async () => {
    await switchUser(page, DEMO.nutritionist);
    await byTestId(page, 'tab-assignments').click();
    await searchPending(page, email);
    await pendingRow().click();
    await chooseOption(page, 'select-nutrition-plan', 'Déficit moderado alto en proteínas');
    await byTestId(page, 'assign-nutrition-button').click();
    await acceptAlert(page, 'Asignar');
    await expect(page).toHaveURL(/\/app\/assignments$/);
  });

  await test.step('the client finds the plans and the answer of the trainer', async () => {
    await switchUser(page, email, PASSWORD);
    await expect(page).toHaveURL(/\/app\/training$/);
    await expect(page.locator('ion-tab-button')).toHaveCount(4);
    await expect(byTestId(page, 'plan-name')).toHaveText('Quema grasa 3 días');
    const entry = byTestId(page, 'notes-entry');
    await expect(entry).toContainText('1 nota nueva de tu equipo');
    await entry.click();
    await expect(byTestId(page, 'notes-thread')).toContainText('Ya lo tienes, ¡a entrenar!');
  });

  await test.step('first workout: sets with load, every exercise and completion', async () => {
    await byTestId(page, 'tab-training').click();
    await page
      .locator('[data-testid^="plan-workout-"][data-status="available"]')
      .filter({ visible: true })
      .click();
    await expect(page).toHaveURL(/\/workouts\/\d+$/);
    await byTestId(page, 'sets-toggle-1').click();
    await fill(page, 'set-weight-1-0', '20');
    await byTestId(page, 'save-sets-1').click();
    await expect(byTestId(page, 'logged-sets-1')).toContainText('× 20 kg');

    const checks = page.locator('[data-testid^="check-exercise-"]').filter({ visible: true });
    for (let index = 0; index < (await checks.count()); index += 1) {
      const check = checks.nth(index);
      if (!(await check.evaluate((element) => element.classList.contains('checkbox-checked')))) {
        await check.click();
      }
    }
    await expect(byTestId(page, 'day-progress')).toHaveAttribute('data-percent', '100');
    await byTestId(page, 'complete-workout').click();
    const alert = page.getByTestId('completion-alert');
    await expect(alert).toContainText('¡Entrenamiento completado!');
    await expect(alert).toContainText('Primer paso'); // first badge
    await alert.locator('button').click();
    await expect(page).toHaveURL(/\/app\/training$/);
    await expect(byTestId(page, 'plan-workout-2')).toHaveAttribute('data-status', 'available');
  });

  await test.step('progress: session, record and weight', async () => {
    await byTestId(page, 'tab-progress').click();
    await byTestId(page, 'segment-workout').click();
    await expect(byTestId(page, 'sessions-counter')).toHaveText('1 sesión completada');
    await expect(byTestId(page, 'records-card')).toContainText('× 20 kg');
    await byTestId(page, 'segment-weight').click();
    await fill(page, 'field-weightKg', '81.5');
    await byTestId(page, 'add-weight').click();
    await expect(byTestId(page, 'weight-list')).toContainText('81,5');
  });

  await test.step('nutrition: menu, diary copied from the menu and shopping list', async () => {
    await byTestId(page, 'tab-nutrition').click();
    await expect(byTestId(page, 'diet-title')).toHaveText('Dieta alta en proteínas');
    await expect(byTestId(page, 'menu-view')).toBeVisible();
    await byTestId(page, 'open-food-diary').click();
    await byTestId(page, 'diary-copy-day').click();
    await expect(
      byTestId(page, 'diary-meal-dinner').locator('[data-testid^="diary-entry-"]').first(),
    ).toBeVisible();
    await expect(byTestId(page, 'diary-summary-text')).toContainText('1 día anotado de 7');

    await page.goto('/app/nutrition/shopping-list');
    await expect(byTestId(page, 'shopping-pending')).toContainText(/Te faltan \d+ productos/);
  });

  await test.step('profile: reminders and export of every personal record', async () => {
    await byTestId(page, 'tab-profile').click();
    await byTestId(page, 'reminders-enabled').click();
    await fill(page, 'reminders-time', '19:30');
    await byTestId(page, 'save-reminders').click();
    await expect(page.getByText('Recordatorios guardados')).toBeVisible();

    const [download] = await Promise.all([
      page.waitForEvent('download'),
      byTestId(page, 'privacy-export').click(),
    ]);
    const exported = JSON.parse(readFileSync((await download.path())!, 'utf8'));
    expect(exported.account.email).toBe(email);
    expect(exported.account.email_verified_at).toBeTruthy();
    expect(exported.reminders).toEqual({ enabled: true, training_time: '19:30' });
    expect(exported.workout_sessions).toHaveLength(1);
    expect(exported.workout_sessions[0].exercises[0].sets[0].weight_kg).toBe(20);
    expect(exported.notes.map((note: { body: string }) => note.body)).toEqual([
      '¿Cuándo tendré mi plan?',
      'Ya lo tienes, ¡a entrenar!',
    ]);
    expect(exported.food_log.length).toBeGreaterThan(5);
    expect(exported.badges[0].code).toBe('first_workout');
  });

  await test.step('the staff follow the client: adherence, notes and diary', async () => {
    await switchUser(page, DEMO.trainer);
    await byTestId(page, 'tab-users').click();
    await byTestId(page, 'open-adherence').click();
    await search(page, 'adherence-filter', name);
    const card = page.locator('[data-testid^="adherence-"][data-status]').filter({ visible: true });
    await expect(card).toHaveCount(1);
    await expect(card).toHaveAttribute('data-status', 'on_track');
    await expect(card).toContainText('Último entreno: hoy');
    await card.click();
    await expect(byTestId(page, 'client-adherence')).toBeVisible();
    await expect(
      byTestId(page, 'client-notes').getByTestId('notes-thread').locator('li'),
    ).toHaveCount(2);
    await expect(byTestId(page, 'diary-summary')).toContainText('1 día anotado de 7');
  });

  await test.step('the admin sees the client in the users and the statistics', async () => {
    await switchUser(page, DEMO.admin);
    await byTestId(page, 'tab-statistics').click();
    await expect(byTestId(page, 'kpi-clients')).toBeVisible();
    await byTestId(page, 'tab-users').click();
    await search(page, 'open-adherence', name);
    const cards = page.locator('[data-testid^="user-card-"]').filter({ visible: true });
    await expect(cards).toHaveCount(1);
    await expect(cards).toContainText(fullName);
  });

  await test.step('the client deletes the account and every record goes', async () => {
    await switchUser(page, email, PASSWORD);
    await byTestId(page, 'tab-profile').click();
    await byTestId(page, 'privacy-delete').click();
    await fill(page, 'delete-password', PASSWORD);
    await page.getByTestId('delete-account-modal').getByTestId('delete-confirm').click();
    await expect(page).toHaveURL(/\/welcome$/);
    const relogin = await page.request.post('/api/v1/auth/login', {
      data: { email, password: PASSWORD },
    });
    expect(relogin.status()).toBe(401);
  });

  expect(await problems()).toEqual([]);
});
