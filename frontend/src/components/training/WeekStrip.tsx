import { IonIcon } from '@ionic/react';
import { checkmark } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import type { WeekDay } from '../../api/types';
import { parseDate, weekdayLabel, weekdayName } from '../../i18n/format';

type DayState = 'done' | 'planned' | 'missed' | 'rest';

const stateOf = (day: WeekDay, today: string): DayState => {
  if (day.completed) return 'done';
  if (!day.scheduled) return 'rest';
  return day.date < today ? 'missed' : 'planned';
};

/** This week, Monday to Sunday: trained days, the ones still to come and the ones skipped. */
export const WeekStrip = ({ days, today }: { days: WeekDay[]; today: string }) => {
  const { t, i18n } = useTranslation();
  const states = days.map((day) => stateOf(day, today));

  return (
    <div className="stack" style={{ gap: 8 }}>
      <ol className="week-strip" aria-label={t('training.week.label')} data-testid="week-strip">
        {days.map((day, index) => {
          const state = states[index];
          const isToday = day.date === today;
          return (
            <li
              key={day.date}
              className={`week-day week-day--${state}${isToday ? ' week-day--today' : ''}`}
              data-testid={`week-day-${index}`}
              data-state={state}
            >
              <span className="week-day__name" aria-hidden="true">
                {weekdayLabel(index, i18n.language, 'short')}
              </span>
              <span className="week-day__dot" aria-hidden="true">
                {state === 'done' ? <IonIcon icon={checkmark} /> : parseDate(day.date).getDate()}
              </span>
              <span className="visually-hidden">
                {`${weekdayName(day.date, i18n.language)}: ${t(`training.week.${state}`)}`}
                {isToday && `, ${t('training.week.today')}`}
              </span>
            </li>
          );
        })}
      </ol>
      <ul className="week-legend" aria-hidden="true">
        {(['done', 'planned', 'missed'] as const)
          .filter((state) => states.includes(state))
          .map((state) => (
            <li key={state}>
              <span className={`week-legend__mark week-legend__mark--${state}`} />
              {t(`training.week.${state}`)}
            </li>
          ))}
      </ul>
    </div>
  );
};
