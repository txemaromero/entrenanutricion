import ca from './locales/ca.json';
import en from './locales/en.json';
import es from './locales/es.json';
import { MANIFESTS } from './index';

const files = import.meta.glob('../../public/manifest*.webmanifest', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>;

const manifest = (url: string) =>
  JSON.parse(files[`../../public${url}`]) as Record<string, unknown>;
const texts = { es, en, ca };

describe('manifests of the installed app', () => {
  it('there is one per language with its description, and the rest is the same', () => {
    const reference = manifest(MANIFESTS.es);
    for (const language of ['es', 'en', 'ca'] as const) {
      const current = manifest(MANIFESTS[language]);
      expect(current.lang).toBe(language);
      expect(current.description).toBe(texts[language].app.description);
      expect({ ...current, lang: '', description: '' }).toEqual({
        ...reference,
        lang: '',
        description: '',
      });
    }
  });
});
