import {
  IonButton,
  IonCard,
  IonCardContent,
  IonChip,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
} from '@ionic/react';
import { createOutline } from 'ionicons/icons';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { catalogApi } from '../../api/staff';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { MediaCarousel } from '../../components/training/MediaCarousel';
import { useResource } from '../../hooks/useResource';

const EditButton = ({ href }: { href: string }) => {
  const { t } = useTranslation();
  return (
    <IonButton
      routerLink={href}
      className="icon-button"
      aria-label={t('common.edit')}
      data-testid="detail-edit"
    >
      <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
    </IonButton>
  );
};

const Block = ({ title, children }: { title: string; children: ReactNode }) => (
  <section>
    <h2 className="section-title">{title}</h2>
    {children}
  </section>
);

const Text = ({ title, text }: { title: string; text: string }) =>
  text ? (
    <Block title={title}>
      <p style={{ margin: 0 }}>{text}</p>
    </Block>
  ) : null;

const Cover = ({ url, kind }: { url: string | null; kind: string | null }) =>
  url ? (
    kind === 'video' ? (
      <video src={url} controls style={{ width: '100%', borderRadius: 12 }} />
    ) : (
      <img
        src={url}
        alt=""
        style={{ width: '100%', maxHeight: 260, objectFit: 'cover', borderRadius: 12 }}
      />
    )
  ) : null;

export const ExerciseDetailStaffPage = () => {
  const { t } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { data, error, loading, reload } = useResource(() => catalogApi.exercises.get(id), [id]);
  return (
    <PageLayout
      title={data?.name ?? t('exercise.title')}
      backHref={`${PATHS.catalog}?tab=exercises`}
      actions={<EditButton href={`${PATHS.catalog}/exercises/${id}/edit`} />}
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="exercise-detail">
          <h1 style={{ margin: 0 }}>{data.name}</h1>
          {!data.isActive && <IonChip color="medium">{t('catalog.inactive')}</IonChip>}
          <p className="muted">{data.description}</p>
          <div className="row row--wrap">
            {data.muscleGroups.map((group) => (
              <IonChip key={group.id} color="tertiary">
                {t(`enums.muscleGroup.${group.slug}`, { defaultValue: group.name })}
              </IonChip>
            ))}
          </div>
          <MediaCarousel media={data.media} title={data.name} />
          {data.steps.length > 0 && (
            <Block title={t('exercise.steps')}>
              <ol>
                {data.steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </Block>
          )}
          <Text title={t('exercise.technique')} text={data.technique} />
          <Text title={t('exercise.commonMistakes')} text={data.commonMistakes} />
          <Text title={t('exercise.benefits')} text={data.benefits} />
        </div>
      )}
    </PageLayout>
  );
};

export const WorkoutDetailPage = () => {
  const { t } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { data, error, loading, reload } = useResource(() => catalogApi.workouts.get(id), [id]);
  return (
    <PageLayout
      title={data?.name ?? t('catalog.tabs.workouts')}
      backHref={`${PATHS.catalog}?tab=workouts`}
      actions={<EditButton href={`${PATHS.catalog}/workouts/${id}/edit`} />}
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="workout-detail">
          <Cover url={data.mediaUrl} kind={data.mediaKind} />
          <h1 style={{ margin: 0 }}>{data.name}</h1>
          <p className="muted">{data.description}</p>
          <IonCard>
            <IonCardContent className="row row--between">
              <span>
                <strong>{data.estimatedDurationMinutes}</strong> {t('common.minutes')}
              </span>
              <span>
                <strong>{data.totalSets}</strong> {t('training.sets')}
              </span>
              <span>
                <strong>{data.totalReps}</strong> {t('training.reps')}
              </span>
            </IonCardContent>
          </IonCard>
          <Block title={t('catalog.exercisesSection')}>
            <IonList>
              {data.exercises.map((item) => (
                <IonItem
                  key={item.id}
                  routerLink={`${PATHS.catalog}/exercises/${item.exercise.id}`}
                  detail
                >
                  <IonLabel>
                    <h3>
                      {item.order}. {item.exercise.name}
                    </h3>
                    <p>
                      {t('training.setsByReps', { sets: item.sets, reps: item.reps })} ·{' '}
                      {t('training.restSeconds', { seconds: item.restSeconds })}
                    </p>
                  </IonLabel>
                </IonItem>
              ))}
            </IonList>
          </Block>
        </div>
      )}
    </PageLayout>
  );
};

export const PlanDetailPage = () => {
  const { t } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { data, error, loading, reload } = useResource(() => catalogApi.plans.get(id), [id]);
  return (
    <PageLayout
      title={data?.name ?? t('catalog.tabs.plans')}
      backHref={`${PATHS.catalog}?tab=plans`}
      actions={<EditButton href={`${PATHS.catalog}/plans/${id}/edit`} />}
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="plan-detail">
          <Cover url={data.mediaUrl} kind={data.mediaKind} />
          <h1 style={{ margin: 0 }}>{data.name}</h1>
          {!data.isActive && <IonChip color="medium">{t('catalog.inactive')}</IonChip>}
          <p className="muted">{data.description}</p>
          <IonList>
            <IonItem>
              <IonLabel>{t('profile.goal')}</IonLabel>
              <IonLabel slot="end">{t(`enums.goal.${data.goal}`)}</IonLabel>
            </IonItem>
            <IonItem>
              <IonLabel>{t('catalog.difficulty')}</IonLabel>
              <IonLabel slot="end">{t(`enums.difficulty.${data.difficulty}`)}</IonLabel>
            </IonItem>
            <IonItem>
              <IonLabel>{t('catalog.equipment')}</IonLabel>
              <IonLabel slot="end">{t(`enums.equipment.${data.equipment}`)}</IonLabel>
            </IonItem>
            <IonItem>
              <IonLabel>{t('catalog.frequency')}</IonLabel>
              <IonLabel slot="end">
                {t('onboarding.daysOption', { count: data.sessionsPerWeek })}
              </IonLabel>
            </IonItem>
            <IonItem>
              <IonLabel>{t('catalog.durationWeeks')}</IonLabel>
              <IonLabel slot="end">{t('training.weeks', { count: data.durationWeeks })}</IonLabel>
            </IonItem>
          </IonList>
          <Block title={t('catalog.workoutSequence')}>
            <IonList>
              {data.workouts.map((row) => (
                <IonItem
                  key={row.id}
                  routerLink={`${PATHS.catalog}/workouts/${row.workout.id}`}
                  detail
                >
                  <IonLabel>
                    <h3>
                      {row.order}. {row.workout.name}
                    </h3>
                    <p>
                      {t('catalog.workoutStats', {
                        count: row.workout.exerciseCount,
                        minutes: row.workout.estimatedDurationMinutes,
                      })}
                    </p>
                  </IonLabel>
                </IonItem>
              ))}
            </IonList>
          </Block>
        </div>
      )}
    </PageLayout>
  );
};
