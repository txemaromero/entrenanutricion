import { expect, test, type Page } from '@playwright/test';

import { DEMO, byTestId, login, search, switchUser } from './helpers';

const openDemoClient = async (page: Page) => {
  await byTestId(page, 'tab-users').click();
  await search(page, 'open-adherence', 'Lucía');
  await page
    .locator('[data-testid^="user-card-"]')
    .filter({ visible: true, hasText: 'Lucía Fernández' })
    .getByTestId('action-view')
    .click();
  await expect(byTestId(page, 'client-notes')).toBeVisible();
};

const write = async (page: Page, text: string) => {
  await byTestId(page, 'note-body').locator('textarea').fill(text);
  await byTestId(page, 'send-note').click();
  await expect(page.getByText('Nota enviada')).toBeVisible();
};

test('the trainer writes, the client reads and answers, the team sees the answer', async ({
  page,
}) => {
  const stamp = Date.now();
  const question = `¿Qué tal la semana? (${stamp})`;
  const answer = `Muy bien, gracias (${stamp})`;

  await login(page, DEMO.trainer);
  await openDemoClient(page);
  await write(page, question);
  const sent = byTestId(page, 'notes-thread').locator('li').filter({ hasText: question });
  await expect(sent).toHaveAttribute('data-mine', 'true');

  // The client sees the new note on the training plan and opens the thread.
  await switchUser(page, DEMO.activeClient);
  const entry = byTestId(page, 'notes-entry');
  await expect(entry).toContainText(/notas? nuevas? de tu equipo/);
  await entry.click();
  await expect(page).toHaveURL(/\/app\/profile\/notes$/);
  const received = byTestId(page, 'notes-thread').locator('li').filter({ hasText: question });
  await expect(received).toContainText('Marc Vidal (Entrenador)');
  await expect(received).toContainText('Nueva');
  await write(page, answer);
  await expect(
    byTestId(page, 'notes-thread').locator('li').filter({ hasText: answer }),
  ).toHaveAttribute('data-mine', 'true');

  // Read: the training plan no longer announces new notes.
  await byTestId(page, 'tab-training').click();
  await expect(byTestId(page, 'plan-progress')).toBeVisible();
  await expect(byTestId(page, 'notes-entry')).toHaveCount(0);

  // The nutritionist finds the answer in the inbox of unread notes.
  await switchUser(page, DEMO.nutritionist);
  await byTestId(page, 'tab-users').click();
  const inbox = byTestId(page, 'notes-inbox');
  await expect(inbox).toContainText(answer);
  await inbox.locator('ion-item').filter({ hasText: answer }).click();
  await expect(
    byTestId(page, 'notes-thread').locator('li').filter({ hasText: answer }),
  ).toContainText('Nueva');
});
