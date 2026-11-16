import { expect, type Page } from '@playwright/test';

export const DEMO_PASSWORD = 'entrenanutricion#2025';

export const DEMO = {
  admin: 'admin@entrenanutricion.dev',
  trainer: 'trainer@entrenanutricion.dev',
  nutritionist: 'nutri@entrenanutricion.dev',
  activeClient: 'cliente@entrenanutricion.dev',
  waitingClient: 'pendiente@entrenanutricion.dev',
} as const;

/** Ionic keeps previous pages in the DOM (hidden): only target what is on screen. */
export const byTestId = (page: Page, testId: string) =>
  page.getByTestId(testId).filter({ visible: true });

/** Click the only visible element with this test id: right after a tab change both pages can be
 * visible for a moment (two "add" buttons, for example). */
export const clickOne = async (page: Page, testId: string) => {
  const target = byTestId(page, testId);
  await expect(target).toHaveCount(1);
  await target.click();
};

/** Type into an Ionic input (the real <input> lives inside <ion-input>). */
export const fill = async (page: Page, testId: string, value: string) => {
  await byTestId(page, testId).locator('input, textarea').first().fill(value);
};

/** Type in the search box of the page that `marker` identifies. Most staff lists have a search box,
 * and during a page transition the page that leaves keeps its own on screen for a moment: wait for
 * the new page and for a single box, or the fill finds two boxes (or the old one). */
export const search = async (page: Page, marker: string, value: string) => {
  await expect(byTestId(page, marker)).toBeVisible();
  const box = byTestId(page, 'search');
  await expect(box).toHaveCount(1);
  await box.locator('input').fill(value);
};

export const login = async (page: Page, email: string, password = DEMO_PASSWORD) => {
  await page.goto('/login');
  await fill(page, 'field-email', email);
  await fill(page, 'field-password', password);
  await byTestId(page, 'login-submit').click();
  await expect(page).not.toHaveURL(/\/login$/);
};

export const selectedTabs = (page: Page) => page.locator('ion-tab-button.tab-selected');

/** Pick an option of an IonSelect rendered with the popover interface. */
export const chooseOption = async (page: Page, testId: string, label: string) => {
  // A click that lands while the form is still settling may not open the popover: retry it.
  await expect(async () => {
    await byTestId(page, testId).click();
    await expect(page.locator('ion-select-popover')).toBeVisible({ timeout: 2_000 });
  }).toPass({ timeout: 15_000 });
  const option = page.locator('ion-select-popover ion-radio').filter({ hasText: label }).first();
  await option.click();
  await expect(page.locator('ion-select-popover')).toHaveCount(0);
};

/** Log out by dropping the stored session, then log in as someone else. */
export const switchUser = async (page: Page, email: string, password = DEMO_PASSWORD) => {
  // The refresh token is an httpOnly cookie: drop it with the session flag.
  await page.context().clearCookies();
  await page.evaluate(() => {
    localStorage.removeItem('entrenanutricion.session');
    sessionStorage.clear();
  });
  await page.goto('/login');
  await expect(page).toHaveURL(/\/login$/);
  await login(page, email, password);
};

/** Accept an IonAlert by the text of its confirm button. */
export const acceptAlert = async (page: Page, buttonText: string) => {
  const alert = page.locator('ion-alert');
  await expect(alert).toBeVisible();
  await alert.locator('button', { hasText: buttonText }).click();
  await expect(alert).toHaveCount(0);
};

/** Assignments show the 100 oldest pending clients: search the one a test has just created. */
export const searchPending = (page: Page, email: string) =>
  byTestId(page, 'assignments-search').locator('input').fill(email);

export const uniqueEmail = (prefix: string) =>
  `${prefix}.${Date.now()}.${Math.floor(Math.random() * 1000)}@example.com`;

/** Register a client and complete the onboarding form; ends on the waiting screen. */
export const registerAndOnboard = async (page: Page, email: string, firstName = 'Prueba') => {
  await page.goto('/register');
  await fill(page, 'field-firstName', firstName);
  await fill(page, 'field-lastName', 'Automática');
  await fill(page, 'field-email', email);
  await fill(page, 'field-password', 'Str0ng#Pass');
  await fill(page, 'field-birthDate', '10031995');
  await chooseOption(page, 'field-gender', 'Mujer');
  await byTestId(page, 'field-termsAccepted').click();
  await byTestId(page, 'field-healthDataConsent').click();
  await expect(byTestId(page, 'register-submit')).not.toHaveAttribute('aria-disabled', 'true');
  await byTestId(page, 'register-submit').click();
  await expect(page).toHaveURL(/\/onboarding$/);

  // 1. Personal data
  await fill(page, 'field-heightCm', '170');
  await fill(page, 'field-initialWeightKg', '82');
  await byTestId(page, 'onboarding-next').click();
  // 2. Goals
  await byTestId(page, 'option-goal-lose_weight').click();
  await chooseOption(page, 'field-dailyTrainingTime', 'Entre 1 y 2 horas');
  await fill(page, 'field-targetChange', '5');
  await byTestId(page, 'onboarding-next').click();
  // 3. Physical activity
  await byTestId(page, 'option-physicalActivityLevel-moderate').click();
  await byTestId(page, 'option-usualExerciseTypes-strength').click();
  await byTestId(page, 'option-availableEquipment-full_gym').click();
  await byTestId(page, 'onboarding-next').click();
  // 4. Diet
  await chooseOption(page, 'field-dietType', 'Omnívora');
  await byTestId(page, 'option-foodRestrictions-none').click();
  await chooseOption(page, 'field-macronutrientIntakeSelfAssessment', 'Balanceado');
  await byTestId(page, 'onboarding-next').click();
  // 5. Health
  await byTestId(page, 'option-medicalConditions-none').click();
  await byTestId(page, 'option-supplements-none').click();
  await byTestId(page, 'onboarding-next').click();
  // 6. Preferences
  await byTestId(page, 'option-trainingPreference-gym').click();
  await byTestId(page, 'onboarding-next').click();

  await expect(page).toHaveURL(/\/app\/status$/);
};
