import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { LANGUAGES, storeLanguage, type Language } from './index';

/** Current language and an instant, persisted switch (also sent as Accept-Language). */
export const useLanguage = () => {
  const { i18n } = useTranslation();
  const changeLanguage = useCallback(
    async (language: Language) => {
      await i18n.changeLanguage(language);
      storeLanguage(language);
    },
    [i18n],
  );
  return {
    language: (i18n.resolvedLanguage ?? i18n.language) as Language,
    languages: LANGUAGES,
    changeLanguage,
  };
};
