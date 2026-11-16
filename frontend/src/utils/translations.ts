import type { CatalogTranslations, TranslatedTexts, TranslationsInput } from '../api/types';

/** Languages the staff translate the catalog into (Spanish is the base text). */
export const TRANSLATION_LANGUAGES = ['en', 'ca'] as const;
export type TranslationLanguage = (typeof TRANSLATION_LANGUAGES)[number];

export const EMPTY_TRANSLATIONS: TranslationsInput = { en: {}, ca: {} };

/** The Spanish text of a field to edit it (the top-level fields come in the screen's language). */
export const baseText = (
  item: { translations?: CatalogTranslations },
  key: keyof TranslatedTexts,
  fallback: string,
) => {
  const value = item.translations?.es?.[key];
  return typeof value === 'string' ? value : fallback;
};

/** The translations of an item as form values (copies; steps only for exercises). */
export const translationsForm = (
  translations?: CatalogTranslations,
  { steps = false }: { steps?: boolean } = {},
): TranslationsInput => {
  const copy = (texts?: TranslatedTexts): TranslatedTexts => {
    const { steps: translatedSteps, ...rest } = texts ?? {};
    return steps ? { ...rest, steps: [...(translatedSteps ?? [])] } : rest;
  };
  return { en: copy(translations?.en), ca: copy(translations?.ca) };
};
