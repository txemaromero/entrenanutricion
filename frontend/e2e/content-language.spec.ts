import { expect, test, type Page } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, fill, login } from './helpers';

const chooseLanguage = async (page: Page, language: 'es' | 'en' | 'ca') => {
  await byTestId(page, 'language-menu').click();
  await page.getByTestId(`language-option-${language}`).click();
  await expect(page.locator('html')).toHaveAttribute('lang', language);
};

test('the catalog follows the language of the app', async ({ page }) => {
  await login(page, DEMO.activeClient);
  await expect(byTestId(page, 'plan-name')).toHaveText('Quema grasa 3 días');
  try {
    await chooseLanguage(page, 'en');
    await expect(byTestId(page, 'plan-name')).toHaveText('Fat burn 3 days');
    await byTestId(page, 'tab-nutrition').click();
    await expect(byTestId(page, 'menu-view')).toContainText('Chicken breast');

    await chooseLanguage(page, 'ca');
    await expect(byTestId(page, 'menu-view')).toContainText('Pit de pollastre');
  } finally {
    await chooseLanguage(page, 'es');
  }
  await expect(byTestId(page, 'menu-view')).toContainText('Pechuga de pollo');
});

test('the trainer translates an exercise and English users see it', async ({ page }) => {
  await login(page, DEMO.trainer);
  const session = await page.request.post('/api/v1/auth/login', {
    data: { email: DEMO.trainer, password: DEMO_PASSWORD },
  });
  const headers = {
    Authorization: `Bearer ${((await session.json()) as { access: string }).access}`,
  };
  const list = (await (
    await page.request.get('/api/v1/exercises', { headers, params: { search: 'Zancadas' } })
  ).json()) as { results: { id: number }[] };
  const id = list.results[0].id;
  const original = (await (
    await page.request.get(`/api/v1/exercises/${id}`, { headers })
  ).json()) as {
    translations: { en: Record<string, unknown>; ca: Record<string, unknown> };
  };
  const name = `Walking lunges ${Date.now()}`;

  try {
    await page.goto(`/app/catalog/exercises/${id}/edit`);
    await expect(byTestId(page, 'translations-language')).toBeVisible();
    await expect(byTestId(page, 'translation-en-name')).toContainText('En español: Zancadas');
    await fill(page, 'translation-en-name', name);
    await byTestId(page, 'form-save').click();
    await expect(page.getByText('Cambios guardados')).toBeVisible();

    await chooseLanguage(page, 'en');
    await page.goto(`/app/catalog/exercises/${id}`);
    await expect(page.getByText(name).first()).toBeVisible();
  } finally {
    await page.request.patch(`/api/v1/exercises/${id}`, {
      headers,
      data: { translations: { en: original.translations.en, ca: original.translations.ca } },
    });
    await chooseLanguage(page, 'es');
  }
});
