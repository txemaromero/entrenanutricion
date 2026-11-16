import { expect, test } from '@playwright/test';

import { byTestId, chooseOption, fill, registerAndOnboard, uniqueEmail } from './helpers';

test('editing the profile is reflected immediately (regression #6)', async ({ page }) => {
  await registerAndOnboard(page, uniqueEmail('e2e.perfil'), 'Inés');
  await byTestId(page, 'tab-profile').click();
  await expect(byTestId(page, 'profile-name')).toHaveText('Inés Automática');
  await expect(byTestId(page, 'profile-goal')).toHaveText('Perder peso');

  await byTestId(page, 'profile-edit').click();
  await fill(page, 'field-firstName', 'Irene');
  await fill(page, 'field-currentWeightKg', '80.5');
  await chooseOption(page, 'field-goal', 'Mantener el peso');
  await byTestId(page, 'profile-save').click();

  await expect(page).toHaveURL(/\/app\/profile$/);
  await expect(byTestId(page, 'profile-name')).toHaveText('Irene Automática');
  await expect(byTestId(page, 'profile-goal')).toHaveText('Mantener el peso');
  await expect(byTestId(page, 'profile-current-weight')).toHaveText('80,5 kg');
});

test('changing the password validates and keeps the session', async ({ page }) => {
  // Not "password" in the address: the new password would look like it (password_too_similar).
  await registerAndOnboard(page, uniqueEmail('e2e.clave'));
  await byTestId(page, 'tab-profile').click();
  await byTestId(page, 'profile-edit').click();
  await byTestId(page, 'open-password-modal').click();
  const modal = page.getByTestId('password-modal');

  await modal.getByTestId('field-currentPassword').locator('input').fill('Wrong#Pass1');
  await modal.getByTestId('field-newPassword').locator('input').fill('N3w#Password');
  await modal.getByTestId('field-confirmPassword').locator('input').fill('Different#1');
  await modal.getByTestId('password-confirm').click();
  await expect(modal).toContainText('Las contraseñas no coinciden.');

  await modal.getByTestId('field-confirmPassword').locator('input').fill('N3w#Password');
  await modal.getByTestId('password-confirm').click();
  await expect(modal).toContainText('La contraseña actual es incorrecta.');

  await modal.getByTestId('field-currentPassword').locator('input').fill('Str0ng#Pass');
  await modal.getByTestId('password-confirm').click();
  await expect(page.locator('ion-toast')).toContainText('Contraseña actualizada');

  await page.reload();
  await expect(page).not.toHaveURL(/\/login$/);
});
