import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCheckbox,
  IonProgressBar,
  IonThumbnail,
  useIonAlert,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useHistory, useParams } from 'react-router-dom';

import { trainingApi } from '../../api/client-features';
import type { DayExercise, SetEntry, WorkoutDay } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { SetsEditor } from '../../components/training/SetsEditor';
import { useResource } from '../../hooks/useResource';
import { saveExerciseMark, withMark } from '../../offline/marks';
import { useOnline } from '../../offline/useOnline';
import { errorMessage } from '../../utils/errors';
import { newBadgesText } from '../../utils/badges';
import { newRecordsText } from '../../utils/sets';
import { motivationText } from '../../utils/training';

/** Workout of the day (US-06): persisted checkboxes, summary and completion. */
const WorkoutDayPage = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const workoutId = Number(id);
  const history = useHistory();
  const router = useIonRouter();
  const [toast] = useIonToast();
  const [presentAlert] = useIonAlert();
  const [completing, setCompleting] = useState(false);
  const online = useOnline();
  const {
    data: day,
    error,
    loading,
    reload,
    setData,
  } = useResource(() => trainingApi.workoutDay(workoutId), [workoutId]);

  const goBackToPlan = () => {
    if (router.canGoBack()) router.goBack();
    else history.replace(PATHS.training);
  };

  /** Tick an exercise (or save its sets, which also ticks it); queued without coverage. */
  const mark = async (
    current: WorkoutDay,
    item: DayExercise,
    completed: boolean,
    sets?: SetEntry[],
  ): Promise<boolean> => {
    setData(withMark(current, item.id, completed, sets));
    try {
      const { day: saved, queued } = await saveExerciseMark(current, item.id, completed, sets);
      setData(saved);
      if (queued) void toast({ message: t('offline.markSaved'), duration: 2000, color: 'medium' });
      else if (sets) void toast({ message: t('sets.saved'), duration: 2000, color: 'success' });
      return true;
    } catch (caught) {
      setData(current);
      void toast({ message: errorMessage(t, caught), duration: 3000, color: 'danger' });
      return false;
    }
  };

  const complete = async () => {
    setCompleting(true);
    try {
      const result = await trainingApi.completeWorkout(workoutId);
      await presentAlert({
        header: result.cycleCompleted
          ? t('training.cycleCompleted')
          : t('training.workoutCompleted'),
        subHeader:
          [newRecordsText(t, result.newRecords, i18n.language), newBadgesText(t, result.newBadges)]
            .filter(Boolean)
            .join(' ') || undefined,
        message: motivationText(t, result.motivation, i18n.language),
        buttons: [{ text: t('training.backToPlan'), role: 'confirm' }],
        onDidDismiss: goBackToPlan,
        htmlAttributes: { 'data-testid': 'completion-alert' },
      });
    } catch (caught) {
      void toast({ message: errorMessage(t, caught), duration: 3000, color: 'danger' });
    } finally {
      setCompleting(false);
    }
  };

  const isCompleted = day?.status === 'completed';
  const canComplete = Boolean(day && !isCompleted && day.progress.percent === 100);

  return (
    <PageLayout
      title={day?.workout.name ?? t('training.workoutOfTheDay')}
      backHref={PATHS.training}
    >
      {loading && !day && <ListSkeleton rows={4} />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {day && (
        <div className="stack">
          <div data-testid="day-progress" data-percent={day.progress.percent}>
            <div className="row row--between">
              <strong>{t('training.dayProgress')}</strong>
              <span>
                {t('training.exercisesDone', {
                  done: day.progress.completed,
                  total: day.progress.total,
                })}{' '}
                · {day.progress.percent}%
              </span>
            </div>
            <IonProgressBar
              value={day.progress.percent / 100}
              aria-label={t('training.dayProgress')}
            />
          </div>

          <IonCard>
            <IonCardContent>
              <div className="row row--between" data-testid="day-summary">
                <span>
                  <strong>{day.summary.estimatedDurationMinutes}</strong> {t('common.minutes')}
                </span>
                <span>
                  <strong>{day.summary.totalSets}</strong> {t('training.sets')}
                </span>
                <span>
                  <strong>{day.summary.totalReps}</strong> {t('training.reps')}
                </span>
              </div>
            </IonCardContent>
          </IonCard>

          <ol className="stack" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {day.exercises.map((item) => (
              <li key={item.id}>
                <IonCard data-testid={`day-exercise-${item.order}`}>
                  <IonCardContent className="stack" style={{ gap: 4 }}>
                    <div className="row">
                      <button
                        type="button"
                        className="row"
                        style={{
                          flex: 1,
                          background: 'none',
                          border: 0,
                          padding: 0,
                          textAlign: 'left',
                          color: 'inherit',
                          minHeight: 44,
                        }}
                        onClick={() =>
                          history.push(
                            `${PATHS.training}/workouts/${workoutId}/exercises/${item.id}`,
                          )
                        }
                        data-testid={`open-exercise-${item.order}`}
                      >
                        {item.exercise.thumbnailUrl && (
                          <IonThumbnail>
                            <img src={item.exercise.thumbnailUrl} alt="" />
                          </IonThumbnail>
                        )}
                        <span>
                          <strong style={{ display: 'block' }}>{item.exercise.name}</strong>
                          <span className="muted">
                            {t('training.setsByReps', { sets: item.sets, reps: item.reps })} ·{' '}
                            {t('training.restSeconds', { seconds: item.restSeconds })}
                          </span>
                        </span>
                      </button>
                      <IonCheckbox
                        checked={item.completed}
                        disabled={isCompleted}
                        onIonChange={(event) => void mark(day, item, event.detail.checked)}
                        aria-label={t('training.markDone', { name: item.exercise.name })}
                        data-testid={`check-exercise-${item.order}`}
                      />
                    </div>
                    <SetsEditor
                      item={item}
                      readOnly={isCompleted}
                      onSave={(sets) => mark(day, item, true, sets)}
                    />
                  </IonCardContent>
                </IonCard>
              </li>
            ))}
          </ol>

          <IonButton
            expand="block"
            size="large"
            disabled={!canComplete || completing || !online}
            onClick={() => void complete()}
            data-testid="complete-workout"
          >
            {isCompleted ? t('enums.workoutStatus.completed') : t('training.completeWorkout')}
          </IonButton>
          {!isCompleted && !canComplete && (
            <p className="muted" style={{ textAlign: 'center' }}>
              {t('training.completeHint')}
            </p>
          )}
          {!isCompleted && canComplete && !online && (
            <p className="muted" style={{ textAlign: 'center' }} data-testid="complete-offline">
              {t('offline.completeNeedsNetwork')}
            </p>
          )}
        </div>
      )}
    </PageLayout>
  );
};

export default WorkoutDayPage;
