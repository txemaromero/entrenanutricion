/** Parse a number typed in a form (accepts a decimal comma); empty → undefined. */
export const toNumber = (value: unknown): number | undefined => {
  const text = String(value ?? '')
    .trim()
    .replace(',', '.');
  return text === '' || Number.isNaN(Number(text)) ? undefined : Number(text);
};
