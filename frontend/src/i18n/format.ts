/** Locale-aware formatting with Intl. Dates from the API are ISO strings. */

const LOCALES: Record<string, string> = { es: 'es-ES', en: 'en-GB', ca: 'ca-ES' };

export const localeOf = (language: string): string => LOCALES[language] ?? 'es-ES';

/** Parse "YYYY-MM-DD" as a local calendar date (not UTC midnight). */
export const parseDate = (value: string): Date => {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day);
};

export const toIsoDate = (date: Date): string =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate(),
  ).padStart(2, '0')}`;

export const formatDate = (
  value: string | Date,
  language: string,
  options: Intl.DateTimeFormatOptions = { day: '2-digit', month: '2-digit', year: 'numeric' },
): string => {
  const date =
    typeof value === 'string' && value.length === 10 ? parseDate(value) : new Date(value);
  return new Intl.DateTimeFormat(localeOf(language), options).format(date);
};

export const formatDateTime = (value: string, language: string): string =>
  formatDate(value, language, { dateStyle: 'medium', timeStyle: 'short' });

export const formatNumber = (
  value: number,
  language: string,
  options: Intl.NumberFormatOptions = { maximumFractionDigits: 1 },
): string => new Intl.NumberFormat(localeOf(language), options).format(value);

export const weekdayName = (value: string, language: string): string =>
  formatDate(value, language, { weekday: 'long', day: 'numeric', month: 'short' });

/** Weekday by index, Monday = 0 like the API (1 January 2024 was a Monday). */
export const weekdayLabel = (
  index: number,
  language: string,
  style: 'long' | 'short' = 'long',
): string =>
  new Intl.DateTimeFormat(localeOf(language), { weekday: style }).format(
    new Date(2024, 0, 1 + index),
  );

export const monthName = (month: number, language: string, style: 'long' | 'short' = 'short') =>
  new Intl.DateTimeFormat(localeOf(language), { month: style }).format(
    new Date(2000, month - 1, 1),
  );

/** "YYYY-MM" moved by `delta` months. */
export const shiftMonth = (month: string, delta: number): string => {
  const [year, monthNumber] = month.split('-').map(Number);
  const date = new Date(year, monthNumber - 1 + delta, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
};
