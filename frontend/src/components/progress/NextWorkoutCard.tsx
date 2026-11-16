import { IonCard, IonCardContent, IonCardHeader, IonCardTitle, IonProgressBar } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import type { Dashboard } from '../../api/types';
import { countdownParts, useNow } from '../../hooks/useNow';
import { weekdayName } from '../../i18n/format';

/** Next workout widget: name, plan % and a live countdown to the scheduled time. */
export const NextWorkoutCard = ({ dashboard }: { dashboard: Dashboard }) => {
  const { t, i18n } = useTranslation();
  const now = useNow(1000);
  const next = dashboard.nextWorkout;
  const parts = next ? countdownParts(new Date(next.targetDatetime), now) : null;

  return (
    <IonCard data-testid="next-workout">
      <IonCardHeader>
        <IonCardTitle>{t('progress.nextWorkout')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        {next && parts ? (
          <>
            <div>
              <strong style={{ fontSize: '1.2rem' }}>{next.workoutName}</strong>
              <p className="muted" style={{ margin: 0 }}>
                {weekdayName(next.scheduledDate, i18n.language)}
              </p>
            </div>
            {parts.done ? (
              <p style={{ fontWeight: 700 }} data-testid="countdown">
                {t('progress.timeToTrain')}
              </p>
            ) : (
              <p
                style={{ fontSize: '1.6rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}
                data-testid="countdown"
                aria-live="off"
              >
                {t('progress.countdown', {
                  days: parts.days,
                  hours: String(parts.hours).padStart(2, '0'),
                  minutes: String(parts.minutes).padStart(2, '0'),
                  seconds: String(parts.seconds).padStart(2, '0'),
                })}
              </p>
            )}
          </>
        ) : (
          <p className="muted">{t('progress.noNextWorkout')}</p>
        )}
        <div>
          <div className="row row--between">
            <span>{dashboard.planName}</span>
            <span>{dashboard.planProgress}%</span>
          </div>
          <IonProgressBar
            value={dashboard.planProgress / 100}
            aria-label={t('training.planProgress')}
          />
        </div>
      </IonCardContent>
    </IonCard>
  );
};
