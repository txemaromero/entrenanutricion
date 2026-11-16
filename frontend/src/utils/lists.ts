/** Return a copy of `items` with the element at `index` moved by `delta` positions. */
export const moveItem = <T>(items: T[], index: number, delta: number): T[] => {
  const target = index + delta;
  if (target < 0 || target >= items.length) return items;
  const copy = [...items];
  const [item] = copy.splice(index, 1);
  copy.splice(target, 0, item);
  return copy;
};

/** Query string value (e.g. `?returnTo=`) from the current location. */
export const queryParam = (search: string, name: string): string | null =>
  new URLSearchParams(search).get(name);

/**
 * `?returnTo=` only to a page of this app (`/app/...`): never another site (`//evil.example`,
 * `/\evil.example`), a `javascript:` URL nor a path with a query or a fragment of its own.
 */
export const returnToParam = (search: string): string | null => {
  const value = queryParam(search, 'returnTo');
  return value !== null && /^\/app(?:\/[\w-]+)*$/.test(value) ? value : null;
};
