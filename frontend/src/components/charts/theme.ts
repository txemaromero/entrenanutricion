import { formatNumber } from '../../i18n/format';
import { cssVar } from './colors';

/** Recessive chrome shared by the charts: hairline grid and muted ticks, from the theme. */
export const chartChrome = () => ({
  grid: cssVar('--en-border', '#e2e6ea'),
  text: cssVar('--en-muted-text', '#5f6b7a'),
  surface: cssVar('--en-surface', '#ffffff'),
});

/** Axis ticks: in full under 10,000 and compact from there (10K, 20K). */
export const axisNumber = (value: number, language: string): string =>
  Math.abs(value) >= 10_000
    ? formatNumber(value, language, { notation: 'compact', maximumFractionDigits: 1 })
    : formatNumber(value, language, { maximumFractionDigits: 1 });

/** `#rrggbb` (or `#rgb`) with an alpha, for area washes; other formats are returned as they are. */
export const withAlpha = (color: string, alpha: number): string => {
  const hex = color.trim().replace('#', '');
  if (!/^([0-9a-f]{3}|[0-9a-f]{6})$/i.test(hex)) return color;
  const full = hex.length === 3 ? [...hex].map((digit) => digit + digit).join('') : hex;
  const [red, green, blue] = [0, 2, 4].map((start) => parseInt(full.slice(start, start + 2), 16));
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
};
