import { IonButton, IonChip, IonIcon, useIonToast, useIonViewDidEnter } from '@ionic/react';
import { checkmarkCircle, ellipseOutline, informationCircleOutline } from 'ionicons/icons';
import { useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { trainingApi } from '../../api/client-features';
import { ApiError } from '../../api/errors';
import type { SetEntry } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { ExerciseInfoModal } from '../../components/training/ExerciseInfoModal';
import { ExerciseProgress } from '../../components/training/ExerciseProgress';
import { MediaCarousel } from '../../components/training/MediaCarousel';
import { RestTimer } from '../../components/training/RestTimer';
import { SetsEditor } from '../../components/training/SetsEditor';
import { useResource } from '../../hooks/useResource';
import { saveExerciseMark } from '../../offline/marks';
import { errorMessage } from '../../utils/errors';

const loadExercise = async (workoutId: number, itemId: number) => {
  const day = await trainingApi.workoutDay(workoutId);
  const item = day.exercises.find((exercise) => exercise.id === itemId);
  if (!item) throw new ApiError({ status: 404, code: 'not_found' });
  const exercise = await trainingApi.exercise(item.exercise.id);
  return { day, item, exercise };
};

/**
 * Exercise detail (US-07): carousel, info modal, big circles, rest timer, sets done, mark as done
 * and the progression of this exercise.
 */
const ExerciseDetailPage = () => {
  const { t } = useTranslation();
  const { id, itemId } = useParams<{ id: string; itemId: string }>();
  const workoutId = Number(id);
  const contentRef = useRef<HTMLIonContentElement>(null);
  const [infoOpen, setInfoOpen] = useState(false);
  const [toast] = useIonToast();
  const { data, error, loading, reload, setData } = useResource(
    () => loadExercise(workoutId, Number(itemId)),
    [workoutId, itemId],
  );

  // Regression #8: always start at the top of the page.
  useIonViewDidEnter(() => {
    void contentRef.current?.scrollToTop(0);
  });

  const mark = async (completed: boolean, sets?: SetEntry[]): Promise<boolean> => {
    if (!data) return false;
    try {
      const { day, queued } = await saveExerciseMark(data.day, data.item.id, completed, sets);
      const item = day.exercises.find((exercise) => exercise.id === data.item.id) ?? data.item;
      setData({ ...data, day, item });
      if (queued) void toast({ message: t('offline.markSaved'), duration: 2000, color: 'medium' });
      else if (sets) void toast({ message: t('sets.saved'), duration: 2000, color: 'success' });
      return true;
    } catch (caught) {
      void toast({ message: errorMessage(t, caught), duration: 3000, color: 'danger' });
      return false;
    }
  };

  const backHref = `${PATHS.training}/workouts/${workoutId}`;
  const locked = data?.day.status === 'completed';

  return (
    <PageLayout
      ref={contentRef}
      title={data?.exercise.name ?? t('exercise.title')}
      backHref={backHref}
      actions={
        data && (
          <IonButton
            className="icon-button"
            onClick={() => setInfoOpen(true)}
            aria-label={t('exercise.infoTitle')}
            data-testid="exercise-info-button"
          >
            <IonIcon slot="icon-only" icon={informationCircleOutline} aria-hidden="true" />
          </IonButton>
        )
      }
    >
      {loading && !data && <ListSkeleton rows={2} />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack">
          <h1 style={{ margin: 0 }} data-testid="exercise-name">
            {data.exercise.name}
          </h1>
          <MediaCarousel media={data.exercise.media} title={data.exercise.name} />
          <div className="row row--wrap" aria-label={t('exercise.muscleGroups')}>
            {data.exercise.muscleGroups.map((group) => (
              <IonChip key={group.id} color="tertiary">
                {t(`enums.muscleGroup.${group.slug}`, { defaultValue: group.name })}
              </IonChip>
            ))}
          </div>
          <div className="big-circles" data-testid="big-circles">
            <div className="big-circle">
              <strong>{data.item.sets}</strong>
              <span>{t('training.sets')}</span>
            </div>
            <div className="big-circle">
              <strong>{data.item.reps}</strong>
              <span>{t('training.reps')}</span>
            </div>
            <div className="big-circle">
              <strong>{data.item.restSeconds}</strong>
              <span>{t('exercise.restUnit')}</span>
            </div>
          </div>
          <RestTimer seconds={data.item.restSeconds} />
          <SetsEditor item={data.item} readOnly={locked} onSave={(sets) => mark(true, sets)} />
          <IonButton
            expand="block"
            color={data.item.completed ? 'success' : 'primary'}
            fill={data.item.completed ? 'solid' : 'outline'}
            disabled={locked}
            onClick={() => void mark(!data.item.completed)}
            data-testid="exercise-mark-done"
            data-done={data.item.completed}
          >
            <IonIcon
              slot="start"
              icon={data.item.completed ? checkmarkCircle : ellipseOutline}
              aria-hidden="true"
            />
            {data.item.completed ? t('exercise.done') : t('exercise.markDone')}
          </IonButton>
          <ExerciseProgress exerciseId={data.exercise.id} name={data.exercise.name} />
          <ExerciseInfoModal
            exercise={data.exercise}
            isOpen={infoOpen}
            onClose={() => setInfoOpen(false)}
          />
        </div>
      )}
    </PageLayout>
  );
};

export default ExerciseDetailPage;
