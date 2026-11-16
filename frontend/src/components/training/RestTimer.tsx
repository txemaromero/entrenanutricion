import { IonButton, IonCard, IonCardContent, IonIcon } from '@ionic/react';
import { pause, play, refresh } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { formatClock, notifyRestFinished, useRestTimer } from '../../hooks/useRestTimer';

/** Rest stopwatch preloaded with the exercise's rest seconds (start, pause, reset). */
export const RestTimer = ({ seconds }: { seconds: number }) => {
  const { t } = useTranslation();
  const timer = useRestTimer(seconds, notifyRestFinished);

  return (
    <IonCard data-testid="rest-timer">
      <IonCardContent className="stack" style={{ alignItems: 'center' }}>
        <h3 style={{ margin: 0 }}>{t('exercise.restTimer')}</h3>
        <time
          style={{ fontSize: '2.6rem', fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}
          aria-label={t('exercise.timeLeft', { seconds: timer.remaining })}
          data-testid="rest-timer-clock"
        >
          {formatClock(timer.remaining)}
        </time>
        <div role="status" aria-live="polite" className="muted">
          {timer.finished ? t('exercise.restFinished') : ''}
        </div>
        <div className="row">
          {timer.running ? (
            <IonButton onClick={timer.pause} color="medium" data-testid="rest-timer-pause">
              <IonIcon slot="start" icon={pause} aria-hidden="true" />
              {t('exercise.pause')}
            </IonButton>
          ) : (
            <IonButton
              onClick={timer.start}
              disabled={timer.remaining === 0}
              data-testid="rest-timer-start"
            >
              <IonIcon slot="start" icon={play} aria-hidden="true" />
              {t('exercise.start')}
            </IonButton>
          )}
          <IonButton fill="outline" onClick={timer.reset} data-testid="rest-timer-reset">
            <IonIcon slot="start" icon={refresh} aria-hidden="true" />
            {t('exercise.reset')}
          </IonButton>
        </div>
      </IonCardContent>
    </IonCard>
  );
};
