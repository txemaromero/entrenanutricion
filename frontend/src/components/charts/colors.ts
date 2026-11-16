/** Read a CSS custom property (theme colours) so charts follow light/dark mode. */
export const cssVar = (name: string, fallback = '#5f6b7a'): string => {
  try {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  } catch {
    return fallback;
  }
};
