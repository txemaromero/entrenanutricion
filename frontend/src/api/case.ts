/** snake_case ↔ camelCase conversion for API payloads (the backend speaks snake_case). */

type Json = unknown;

const isPlainObject = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && Object.getPrototypeOf(value) === Object.prototype;

export const toCamel = (key: string): string =>
  key
    .split('.')
    .map((part) => part.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase()))
    .join('.');

export const toSnake = (key: string): string =>
  key
    .split('.')
    // Every capital starts a word, so one-letter words survive the round trip (vitaminAUg).
    .map((part) => part.replace(/(?<=.)([A-Z])/g, '_$1').toLowerCase())
    .join('.');

const convertKeys = (value: Json, convert: (key: string) => string): Json => {
  if (Array.isArray(value)) return value.map((item) => convertKeys(item, convert));
  if (!isPlainObject(value)) return value;
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [convert(key), convertKeys(item, convert)]),
  );
};

export const camelizeKeys = <T = Json>(value: Json): T => convertKeys(value, toCamel) as T;
export const snakifyKeys = <T = Json>(value: Json): T => convertKeys(value, toSnake) as T;
