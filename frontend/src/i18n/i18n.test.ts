import ca from './locales/ca.json';
import en from './locales/en.json';
import es from './locales/es.json';

type Tree = { [key: string]: string | Tree };

const flatten = (tree: Tree, prefix = ''): Record<string, string> =>
  Object.entries(tree).reduce<Record<string, string>>((all, [key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof value === 'string'
      ? { ...all, [path]: value }
      : { ...all, ...flatten(value, path) };
  }, {});

const locales = { es: flatten(es), en: flatten(en), ca: flatten(ca) };

describe('translations', () => {
  it.each(['en', 'ca'] as const)('%s has exactly the same keys as es', (language) => {
    const reference = Object.keys(locales.es).sort();
    expect(Object.keys(locales[language]).sort()).toEqual(reference);
  });

  it.each(['es', 'en', 'ca'] as const)('%s has no empty values', (language) => {
    const empty = Object.entries(locales[language]).filter(([, value]) => !value.trim());
    expect(empty).toEqual([]);
  });

  it.each(['es', 'en', 'ca'] as const)(
    '%s keeps the same interpolation placeholders',
    (language) => {
      const placeholders = (value: string) => (value.match(/{{\s*\w+\s*}}/g) ?? []).sort();
      const mismatches = Object.entries(locales.es).filter(
        ([key, value]) =>
          JSON.stringify(placeholders(value)) !==
          JSON.stringify(placeholders(locales[language][key])),
      );
      expect(mismatches).toEqual([]);
    },
  );

  it('covers every error code the backend can return', () => {
    const backendCodes = [
      'invalid_credentials',
      'email_taken',
      'workout_locked',
      'training_plan_already_assigned',
      'calories_mismatch',
      'distribution_sum',
      'cannot_delete_self',
    ];
    backendCodes.forEach((code) => expect(locales.es[`errors.${code}`]).toBeTruthy());
  });
});
