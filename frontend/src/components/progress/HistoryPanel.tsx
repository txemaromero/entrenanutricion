import {
  IonCard,
  IonCardContent,
  IonInput,
  IonItem,
  IonLabel,
  IonList,
  IonProgressBar,
  IonSelect,
  IonSelectOption,
} from '@ionic/react';
import { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { progressApi, trainingApi, type HistoryFilters } from '../../api/client-features';
import type { Dashboard } from '../../api/types';
import { useResource } from '../../hooks/useResource';
import { formatDateTime } from '../../i18n/format';
import { EmptyState, ErrorState, ListSkeleton } from '../States';

/** Chronological session history with date/workout filters, plan % and counter. */
export const HistoryPanel = ({ dashboard }: { dashboard: Dashboard }) => {
  const { t, i18n } = useTranslation();
  const [filters, setFilters] = useState<HistoryFilters>({});
  const history = useResource(() => progressApi.history(filters), [JSON.stringify(filters)]);
  const plan = useResource(trainingApi.myPlan);

  const workoutOptions = useMemo(() => {
    const seen = new Map<number, string>();
    plan.data?.workouts.forEach((row) => seen.set(row.workout.id, row.workout.name));
    return [...seen.entries()];
  }, [plan.data]);

  return (
    <div className="stack">
      <IonCard>
        <IonCardContent className="stack">
          <div className="row row--between">
            <strong>{t('training.planProgress')}</strong>
            <span>{dashboard.planProgress}%</span>
          </div>
          <IonProgressBar
            value={dashboard.planProgress / 100}
            aria-label={t('training.planProgress')}
          />
          <p style={{ margin: 0 }} data-testid="sessions-counter">
            {t('progress.sessionsCompleted', { count: dashboard.totalSessions })}
          </p>
        </IonCardContent>
      </IonCard>

      <div
        className="card-grid"
        style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}
      >
        <IonInput
          type="date"
          label={t('progress.from')}
          labelPlacement="floating"
          fill="outline"
          value={filters.from ?? ''}
          onIonChange={(event) =>
            setFilters((current) => ({ ...current, from: event.detail.value ?? undefined }))
          }
          data-testid="history-from"
        />
        <IonInput
          type="date"
          label={t('progress.to')}
          labelPlacement="floating"
          fill="outline"
          value={filters.to ?? ''}
          onIonChange={(event) =>
            setFilters((current) => ({ ...current, to: event.detail.value ?? undefined }))
          }
          data-testid="history-to"
        />
        <IonSelect
          label={t('progress.workoutFilter')}
          labelPlacement="floating"
          fill="outline"
          interface="popover"
          value={filters.workout ?? ''}
          onIonChange={(event) =>
            setFilters((current) => ({ ...current, workout: event.detail.value || undefined }))
          }
          data-testid="history-workout"
        >
          <IonSelectOption value="">{t('progress.allWorkouts')}</IonSelectOption>
          {workoutOptions.map(([id, name]) => (
            <IonSelectOption key={id} value={id}>
              {name}
            </IonSelectOption>
          ))}
        </IonSelect>
      </div>

      {history.loading && !history.data && <ListSkeleton />}
      {history.error && <ErrorState error={history.error} onRetry={history.reload} />}
      {history.data && history.data.results.length === 0 && (
        <EmptyState message={t('progress.noSessions')} />
      )}
      {history.data && history.data.results.length > 0 && (
        <IonList data-testid="history-list">
          {history.data.results.map((session) => (
            <IonItem key={session.id}>
              <IonLabel>
                <h3>{session.workoutName}</h3>
                <p>{formatDateTime(session.completedAt, i18n.language)}</p>
                <p>
                  {t('progress.sessionStats', {
                    sets: session.totalSets,
                    reps: session.totalReps,
                    minutes: session.durationMinutes,
                  })}
                </p>
              </IonLabel>
            </IonItem>
          ))}
        </IonList>
      )}
    </div>
  );
};
