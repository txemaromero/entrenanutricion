import es from './locales/es.json';

/**
 * Regression #3 (labels shown as variable names): every literal key passed to `t('…')` in the
 * source must exist in the translations (plural keys may exist only as `_one` / `_other`).
 */
const sources = import.meta.glob('../**/*.{ts,tsx}', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const lookup = (key: string): unknown =>
  key
    .split('.')
    .reduce<unknown>(
      (node, part) =>
        node && typeof node === 'object' ? (node as Record<string, unknown>)[part] : undefined,
      es,
    );

const exists = (key: string) =>
  typeof lookup(key) === 'string' ||
  (typeof lookup(`${key}_one`) === 'string' && typeof lookup(`${key}_other`) === 'string');

describe('translation keys used in the code', () => {
  const used = new Map<string, string>();
  Object.entries(sources)
    .filter(([path]) => !path.includes('.test.'))
    .forEach(([path, source]) => {
      for (const match of source.matchAll(/\bt\(\s*'([a-zA-Z0-9_.]+)'/g)) used.set(match[1], path);
    });

  it('finds the translation calls', () => {
    expect(used.size).toBeGreaterThan(200);
  });

  it('every literal key exists in es.json', () => {
    const missing = [...used.entries()]
      .filter(([key]) => !exists(key))
      .map(([key, path]) => `${key} (${path})`);
    expect(missing).toEqual([]);
  });
});
