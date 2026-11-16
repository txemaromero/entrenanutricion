import { IonIcon } from '@ionic/react';
import { arrowDown, arrowUp, remove } from 'ionicons/icons';

/** Change against a previous period: an arrow and words (never the colour alone). */
export interface StatTrend {
  direction: 'up' | 'down' | 'flat';
  text: string;
}

export interface StatTile {
  key: string;
  /** Decorative icon (ionicons) next to the figure. */
  icon: string;
  label: string;
  value: string;
  /** Second line in muted ink, e.g. a breakdown. */
  hint?: string;
  trend?: StatTrend;
  /** Test id of the tile (`stat-<key>` by default). */
  testId?: string;
}

const TREND_ICON = { up: arrowUp, down: arrowDown, flat: remove };

/** Headline figures in a responsive grid: an icon, the number in large type and what it is. */
export const StatTiles = ({ items, testId }: { items: StatTile[]; testId?: string }) => (
  <ul className="stat-tiles" data-testid={testId}>
    {items.map((item) => (
      <li className="stat-tile" key={item.key} data-testid={item.testId ?? `stat-${item.key}`}>
        <IonIcon icon={item.icon} className="stat-tile__icon" aria-hidden="true" />
        <span className="stat-tile__value">{item.value}</span>
        <span className="stat-tile__label">{item.label}</span>
        {item.hint && <span className="stat-tile__hint">{item.hint}</span>}
        {item.trend && (
          <span
            className={`stat-tile__trend stat-tile__trend--${item.trend.direction}`}
            data-direction={item.trend.direction}
          >
            <IonIcon icon={TREND_ICON[item.trend.direction]} aria-hidden="true" />
            {item.trend.text}
          </span>
        )}
      </li>
    ))}
  </ul>
);
