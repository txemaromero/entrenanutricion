import { crc32, deflateSync } from 'node:zlib';

import { expect, test } from '@playwright/test';

import {
  DEMO,
  DEMO_PASSWORD,
  byTestId,
  chooseOption,
  clickOne,
  fill,
  login,
  registerAndOnboard,
  uniqueEmail,
} from './helpers';

const TOO_MANY_PIXELS = 'La imagen tiene demasiados píxeles (hasta 40 megapíxeles).';

const chunk = (type: string, data: Buffer) => {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
};

/** A black 1-bit PNG: a few kB on disk, `width × height` pixels once decoded. */
const png = (name: string, width: number, height: number) => {
  const header = Buffer.alloc(13); // colour type 0 (grey); compression, filter and interlace 0
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header.writeUInt8(1, 8); // 1 bit per pixel
  const rows = Buffer.alloc((Math.ceil(width / 8) + 1) * height); // filter byte + pixels, all 0
  const buffer = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', header),
    chunk('IDAT', deflateSync(rows, { level: 9 })),
    chunk('IEND', Buffer.alloc(0)),
  ]);
  return { name, mimeType: 'image/png', buffer };
};

// 48 megapixels in a few kB: the browser lets it through (type and weight are fine).
const bomb = () => png('bomba.png', 8_000, 6_000);

test('a photo with too many pixels is refused next to it; a normal one is saved', async ({
  page,
}) => {
  await registerAndOnboard(page, uniqueEmail('e2e.foto'));
  await byTestId(page, 'tab-profile').click();
  await byTestId(page, 'profile-edit').click();

  await page.getByTestId('photo-input').setInputFiles(bomb());
  await byTestId(page, 'profile-save').click();
  await expect(page.getByText(TOO_MANY_PIXELS).filter({ visible: true })).toBeVisible();

  await page.getByTestId('photo-input').setInputFiles(png('foto.png', 64, 64));
  await byTestId(page, 'profile-save').click();
  await expect(page).toHaveURL(/\/app\/profile$/);
});

test('a workout whose image is refused is created only once', async ({ page }) => {
  const name = `Entreno con portada E2E ${Date.now()}`;
  await login(page, DEMO.trainer);
  await byTestId(page, 'catalog-tab-workouts').click();
  await clickOne(page, 'fab-add');
  await fill(page, 'field-name', name);
  await byTestId(page, 'add-exercise-row').click();
  await chooseOption(page, 'field-exercises.0.exerciseId', 'Aperturas con mancuernas');

  await page.getByTestId('media-input').setInputFiles(bomb());
  await byTestId(page, 'form-save').click();
  await expect(byTestId(page, 'media-error')).toHaveText(TOO_MANY_PIXELS);

  await page.getByTestId('media-input').setInputFiles(png('portada.png', 64, 64));
  await expect(byTestId(page, 'media-error')).toHaveCount(0);
  await byTestId(page, 'form-save').click();
  await expect(byTestId(page, 'workout-detail')).toContainText(name);

  // The second save updated the workout created by the first one.
  const session = await page.request.post('/api/v1/auth/login', {
    data: { email: DEMO.trainer, password: DEMO_PASSWORD },
  });
  const headers = {
    Authorization: `Bearer ${((await session.json()) as { access: string }).access}`,
  };
  const found = (await (
    await page.request.get('/api/v1/workouts', { headers, params: { search: name } })
  ).json()) as { results: { id: number }[] };
  expect(found.results).toHaveLength(1);
  const workout = (await (
    await page.request.get(`/api/v1/workouts/${found.results[0].id}`, { headers })
  ).json()) as { media_url: string | null };
  expect(workout.media_url).toBeTruthy();
});
