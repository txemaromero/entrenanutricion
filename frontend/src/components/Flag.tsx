import type { ReactElement } from 'react';

import type { Language } from '../i18n';

/** Small inline SVG flags (no external assets). Decorative: the language name is always shown. */
const FLAGS: Record<Language, ReactElement> = {
  es: (
    <>
      <rect width="30" height="20" fill="#c60b1e" />
      <rect y="5" width="30" height="10" fill="#ffc400" />
    </>
  ),
  en: (
    <>
      <rect width="30" height="20" fill="#012169" />
      <path d="M0 0l30 20M30 0L0 20" stroke="#fff" strokeWidth="4" />
      <path d="M0 0l30 20M30 0L0 20" stroke="#c8102e" strokeWidth="1.6" />
      <path d="M15 0v20M0 10h30" stroke="#fff" strokeWidth="6" />
      <path d="M15 0v20M0 10h30" stroke="#c8102e" strokeWidth="3.4" />
    </>
  ),
  ca: (
    <>
      <rect width="30" height="20" fill="#fcdd09" />
      {[2.22, 6.66, 11.1, 15.54].map((y) => (
        <rect key={y} y={y} width="30" height="2.22" fill="#da121a" />
      ))}
    </>
  ),
};

export const Flag = ({ language, size = 24 }: { language: Language; size?: number }) => (
  <svg
    width={size}
    height={(size * 2) / 3}
    viewBox="0 0 30 20"
    aria-hidden="true"
    focusable="false"
    style={{ borderRadius: 3, flexShrink: 0 }}
  >
    {FLAGS[language]}
  </svg>
);
