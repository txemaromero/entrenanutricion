import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { meApi } from '../api/me';
import type { AppLanguage, Me } from '../api/types';

const APP_LANGUAGES: readonly string[] = ['es', 'en', 'ca'] satisfies AppLanguage[];

/**
 * Store the language of the app in the account whenever they differ (sign-in, language menu), so
 * the backend writes the emails in it. Without coverage it is retried at the next change.
 */
export const useAccountLanguage = (user: Me | null, onSaved: (me: Me) => void) => {
  const { i18n } = useTranslation();
  const language = i18n.resolvedLanguage ?? i18n.language;
  useEffect(() => {
    if (!user || user.language === language || !APP_LANGUAGES.includes(language)) return;
    meApi
      .updateProfile({ language: language as AppLanguage })
      .then(onSaved)
      .catch(() => undefined);
  }, [user, language, onSaved]);
};
