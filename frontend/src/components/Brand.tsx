import { useTranslation } from 'react-i18next';

/** Logo (dumbbell + leaf) and a decorative welcome illustration, drawn inline. */
export const AppLogo = ({ size = 48 }: { size?: number }) => {
  const { t } = useTranslation();
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label={t('app.name')}
      style={{ margin: '0 auto' }}
    >
      <rect width="64" height="64" rx="16" fill="var(--ion-color-primary)" />
      <path
        d="M12 36h6v-8h-6zm34-8v8h6v-8zM18 24h4v16h-4zm24 0h4v16h-4zM22 30h20v4H22z"
        fill="#fff"
      />
      <path d="M44 12c-8 0-12 5-12 11 6 0 12-3 12-11z" fill="#bdf2cf" />
    </svg>
  );
};

export const HeroIllustration = () => (
  <svg
    viewBox="0 0 320 150"
    width="100%"
    style={{ maxWidth: 360, margin: '0 auto' }}
    aria-hidden="true"
  >
    {/* Training tile: a dumbbell with two plates on each side. */}
    <rect
      x="16"
      y="11"
      width="128"
      height="128"
      rx="28"
      fill="rgba(var(--ion-color-primary-rgb), 0.13)"
    />
    <g transform="translate(80 75) rotate(-30) scale(0.86)">
      <rect x="-44" y="-5" width="88" height="10" rx="5" fill="var(--ion-color-medium)" />
      <rect x="-46" y="-28" width="15" height="56" rx="6" fill="var(--ion-color-primary)" />
      <rect x="31" y="-28" width="15" height="56" rx="6" fill="var(--ion-color-primary)" />
      <rect x="-59" y="-18" width="11" height="36" rx="5" fill="var(--ion-color-primary-tint)" />
      <rect x="48" y="-18" width="11" height="36" rx="5" fill="var(--ion-color-primary-tint)" />
    </g>

    <path
      d="M160 65v20M150 75h20"
      stroke="var(--ion-color-medium)"
      strokeWidth="5"
      strokeLinecap="round"
    />

    {/* Nutrition tile: an apple. */}
    <rect
      x="176"
      y="11"
      width="128"
      height="128"
      rx="28"
      fill="rgba(var(--ion-color-tertiary-rgb), 0.14)"
    />
    <g transform="translate(240 72)">
      <path
        d="M0-15C-8-24-31-22-31 3-31 23-15 35-7 35-3 35-2 33 0 33 2 33 3 35 7 35 15 35 31 23 31 3 31-22 8-24 0-15Z"
        fill="var(--ion-color-tertiary)"
      />
      <path
        d="M-20-3C-20-9-16-13-11-14"
        stroke="#fff"
        strokeOpacity="0.75"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M0-15C0-23 1-27 5-32"
        stroke="var(--ion-color-medium)"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      <path d="M3-22C6-35 19-39 28-37 26-26 15-17 3-22Z" fill="var(--ion-color-primary)" />
    </g>
  </svg>
);
