import { expect, test, type APIRequestContext } from '@playwright/test';

import { DEMO, DEMO_PASSWORD, byTestId, fill, login } from './helpers';

const headersFor = async (request: APIRequestContext) => {
  const session = await request.post('/api/v1/auth/login', {
    data: { email: DEMO.activeClient, password: DEMO_PASSWORD },
    headers: { 'Accept-Language': 'es' },
  });
  return { Authorization: `Bearer ${((await session.json()) as { access: string }).access}` };
};

test('the client chooses the training time and turns the reminders on', async ({ page }) => {
  await login(page, DEMO.activeClient);
  const headers = await headersFor(page.request);
  try {
    await byTestId(page, 'tab-profile').click();
    const card = byTestId(page, 'reminders-card');
    await expect(card).toContainText('Recordatorios de entreno');
    await expect(card).toContainText('Hora por defecto (18:00)');

    await byTestId(page, 'reminders-enabled').click();
    await fill(page, 'reminders-time', '07:30');
    await byTestId(page, 'save-reminders').click();
    await expect(page.getByText('Recordatorios guardados')).toBeVisible();
    await expect(byTestId(page, 'reset-training-time')).toContainText('18:00');

    const saved = (await (await page.request.get('/api/v1/me/reminders', { headers })).json()) as {
      enabled: boolean;
      training_time: string;
    };
    expect(saved).toMatchObject({ enabled: true, training_time: '07:30' });

    // The countdown of the next workout uses the new time.
    const dashboard = (await (
      await page.request.get('/api/v1/me/progress/dashboard', { headers })
    ).json()) as { next_workout: { target_datetime: string } | null };
    if (dashboard.next_workout) {
      expect(dashboard.next_workout.target_datetime).toContain('T07:30:00');
    }

    // The account follows the language of the app (the reminder emails use it).
    await byTestId(page, 'language-menu').click();
    await byTestId(page, 'language-option-en').click();
    await expect(byTestId(page, 'reminders-card')).toContainText('Training reminders');
    await expect
      .poll(async () => {
        const me = (await (await page.request.get('/api/v1/me', { headers })).json()) as {
          language: string;
        };
        return me.language;
      })
      .toBe('en');
  } finally {
    await page.request.put('/api/v1/me/reminders', {
      headers,
      data: { enabled: false, training_time: null },
    });
    await page.request.patch('/api/v1/me/profile', { headers, data: { language: 'es' } });
  }
});
