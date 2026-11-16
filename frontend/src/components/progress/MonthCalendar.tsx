import { IonButton, IonIcon } from '@ionic/react';
import { chevronBack, chevronForward } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { localeOf, shiftMonth, toIsoDate } from '../../i18n/format';

interface MonthCalendarProps {
  /** "YYYY-MM" */
  month: string;
  completedDays: string[];
  scheduledDays: string[];
  onChangeMonth: (month: string) => void;
}

/** Monday-first month grid; completed days filled, scheduled days outlined. */
export const MonthCalendar = ({
  month,
  completedDays,
  scheduledDays,
  onChangeMonth,
}: MonthCalendarProps) => {
  const { t, i18n } = useTranslation();
  const locale = localeOf(i18n.language);
  const [year, monthNumber] = month.split('-').map(Number);
  const first = new Date(year, monthNumber - 1, 1);
  const daysInMonth = new Date(year, monthNumber, 0).getDate();
  const offset = (first.getDay() + 6) % 7; // Monday = 0
  const completed = new Set(completedDays);
  const scheduled = new Set(scheduledDays);
  const today = toIsoDate(new Date());
  const weekdays = Array.from({ length: 7 }, (_, index) =>
    new Intl.DateTimeFormat(locale, { weekday: 'narrow' }).format(new Date(2024, 0, 1 + index)),
  );
  const monthTitle = new Intl.DateTimeFormat(locale, { month: 'long', year: 'numeric' }).format(
    first,
  );
  const title = monthTitle.charAt(0).toLocaleUpperCase(locale) + monthTitle.slice(1);
  // Days of the month padded with empty cells and split into Monday-first weeks.
  const cells: (number | null)[] = [
    ...Array.from({ length: offset }, () => null),
    ...Array.from({ length: daysInMonth }, (_, index) => index + 1),
  ];
  while (cells.length % 7) cells.push(null);
  const weeks = Array.from({ length: cells.length / 7 }, (_, index) =>
    cells.slice(index * 7, index * 7 + 7),
  );

  return (
    <section data-testid="month-calendar">
      <div className="row row--between">
        <IonButton
          fill="clear"
          className="icon-button"
          onClick={() => onChangeMonth(shiftMonth(month, -1))}
          aria-label={t('progress.previousMonth')}
        >
          <IonIcon slot="icon-only" icon={chevronBack} aria-hidden="true" />
        </IonButton>
        <h3 style={{ margin: 0 }}>{title}</h3>
        <IonButton
          fill="clear"
          className="icon-button"
          onClick={() => onChangeMonth(shiftMonth(month, 1))}
          aria-label={t('progress.nextMonth')}
        >
          <IonIcon slot="icon-only" icon={chevronForward} aria-hidden="true" />
        </IonButton>
      </div>
      <div className="calendar" role="grid" aria-label={title}>
        <div className="calendar__row" role="row">
          {weekdays.map((day, index) => (
            <div key={index} className="calendar__weekday" role="columnheader">
              {day}
            </div>
          ))}
        </div>
        {weeks.map((week, weekIndex) => (
          <div key={weekIndex} className="calendar__row" role="row">
            {week.map((day, dayIndex) => {
              if (day === null) return <div key={`empty-${dayIndex}`} role="gridcell" />;
              const iso = toIsoDate(new Date(year, monthNumber - 1, day));
              const isCompleted = completed.has(iso);
              const isScheduled = scheduled.has(iso);
              const classes = [
                'calendar__day',
                isCompleted && 'calendar__day--completed',
                !isCompleted && isScheduled && 'calendar__day--scheduled',
                iso === today && 'calendar__day--today',
              ]
                .filter(Boolean)
                .join(' ');
              const state = isCompleted
                ? t('progress.dayCompleted')
                : isScheduled
                  ? t('progress.dayScheduled')
                  : '';
              return (
                <div
                  key={iso}
                  className={classes}
                  role="gridcell"
                  aria-label={`${day} ${state}`.trim()}
                  data-date={iso}
                  data-state={isCompleted ? 'completed' : isScheduled ? 'scheduled' : 'none'}
                >
                  {day}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <p className="muted row row--wrap" style={{ gap: 16, marginTop: 8 }}>
        <span>
          <span className="legend-swatch" style={{ background: 'var(--ion-color-primary)' }} />
          {t('progress.dayCompleted')}
        </span>
        <span>
          <span
            className="legend-swatch"
            style={{ border: '2px solid var(--ion-color-primary)' }}
          />
          {t('progress.dayScheduled')}
        </span>
      </p>
    </section>
  );
};
