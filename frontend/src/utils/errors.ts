import type { TFunction } from 'i18next';

import { ApiError } from '../api/errors';

/** Translated message for an API error, using its stable `code`. */
export const errorMessage = (t: TFunction, error: unknown): string => {
  const code = error instanceof ApiError ? error.code : 'unknown_error';
  const params = error instanceof ApiError ? error.extra : {};
  return t(`errors.${code}`, { ...params, defaultValue: t('errors.generic') });
};

/** First translated error of a form field returned by the API (field names in camelCase). */
export const apiFieldError = (t: TFunction, error: unknown, field: string): string | undefined => {
  if (!(error instanceof ApiError)) return undefined;
  const code = error.fieldCodes[field]?.[0];
  if (!code) return undefined;
  return t(`errors.${code}`, { defaultValue: error.fields[field]?.[0] ?? t('errors.generic') });
};

/** The file fields of the API: they are not form fields, so their error goes by the picker. */
const UPLOAD_FIELDS = ['photo', 'media', 'file'];

/**
 * Translated API error about an uploaded file, if that is what failed. The browser checks the type
 * and the weight, but not everything (the pixels of an image): the server has the last word.
 */
export const uploadError = (t: TFunction, error: unknown): string | undefined =>
  UPLOAD_FIELDS.map((field) => apiFieldError(t, error, field)).find(Boolean);

/** Translate a Zod message that is already an i18n key. */
export const translateKey = (t: TFunction, key?: string): string | undefined =>
  key ? t(key, { defaultValue: t('errors.generic') }) : undefined;

/** Push the API field errors into a React Hook Form (keys are dotted camelCase paths). */
export const applyServerErrors = (
  error: unknown,
  setError: (name: never, value: { type: string; message: string }) => void,
): boolean => {
  if (!(error instanceof ApiError)) return false;
  const entries = Object.entries(error.fieldCodes);
  entries.forEach(([field, codes]) =>
    setError(field as never, { type: 'server', message: `errors.${codes[0]}` }),
  );
  return entries.length > 0;
};
