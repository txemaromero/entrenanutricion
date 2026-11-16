import type { ReactNode } from 'react';

interface ProgressRingProps {
  /** Share done, 0–1 (more than 1 draws a full ring). */
  ratio: number;
  /** What the ring says, for screen readers. */
  label: string;
  /** Text under the ring. */
  caption?: ReactNode;
  /** Figure in the centre. */
  children?: ReactNode;
  /** CSS custom property with the ring colour. */
  colorVar?: string;
  size?: number;
  testId?: string;
}

/** Circular progress (SVG): a hairline track and an arc rounded at its end. */
export const ProgressRing = ({
  ratio,
  label,
  caption,
  children,
  colorVar = '--ion-color-primary',
  size = 88,
  testId,
}: ProgressRingProps) => {
  const share = Math.max(0, Math.min(Number.isFinite(ratio) ? ratio : 0, 1));
  const stroke = Math.round(size / 10);
  const radius = (size - stroke) / 2;
  const length = 2 * Math.PI * radius;
  const centre = size / 2;

  return (
    <figure className="ring" data-testid={testId} data-ratio={share.toFixed(2)}>
      <div className="ring__dial" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={label}
        >
          <circle
            cx={centre}
            cy={centre}
            r={radius}
            fill="none"
            stroke="var(--en-border)"
            strokeWidth={stroke}
          />
          {share > 0 && (
            <circle
              className="ring__value"
              cx={centre}
              cy={centre}
              r={radius}
              fill="none"
              stroke={`var(${colorVar})`}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={length}
              strokeDashoffset={length * (1 - share)}
              transform={`rotate(-90 ${centre} ${centre})`}
            />
          )}
        </svg>
        <div className="ring__centre" aria-hidden="true">
          {children}
        </div>
      </div>
      {caption && <figcaption className="ring__caption">{caption}</figcaption>}
    </figure>
  );
};
