import { IonChip, IonLabel, IonSegment, IonSegmentButton } from '@ionic/react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useHistory, useLocation } from 'react-router-dom';

import { catalogApi } from '../../api/staff';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { AddFab, ManagementCard, SearchBox } from '../../components/staff/ManagementCard';
import { useDeleteAction } from '../../hooks/useDeleteAction';
import { useResource } from '../../hooks/useResource';
import { queryParam } from '../../utils/lists';

export type CatalogTab = 'workouts' | 'exercises' | 'plans';
const TABS: CatalogTab[] = ['workouts', 'exercises', 'plans'];

const WorkoutsList = ({ search }: { search: string }) => {
  const { t } = useTranslation();
  const remove = useDeleteAction();
  const { data, error, loading, reload } = useResource(
    () => catalogApi.workouts.list({ search }),
    [search],
  );
  if (loading && !data) return <ListSkeleton />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data?.results.length) return <EmptyState />;
  return (
    <div className="card-grid">
      {data.results.map((workout) => (
        <ManagementCard
          key={workout.id}
          testId={`workout-card-${workout.id}`}
          title={workout.name}
          description={workout.description}
          viewHref={`${PATHS.catalog}/workouts/${workout.id}`}
          editHref={`${PATHS.catalog}/workouts/${workout.id}/edit`}
          onDelete={() =>
            void remove({
              name: workout.name,
              remove: () => catalogApi.workouts.remove(workout.id),
              onDone: reload,
            })
          }
        >
          <p className="muted" style={{ margin: 0 }}>
            {t('catalog.workoutStats', {
              count: workout.exerciseCount,
              minutes: workout.estimatedDurationMinutes,
            })}
          </p>
        </ManagementCard>
      ))}
    </div>
  );
};

const ExercisesList = ({ search }: { search: string }) => {
  const { t } = useTranslation();
  const remove = useDeleteAction();
  const { data, error, loading, reload } = useResource(
    () => catalogApi.exercises.list({ search }),
    [search],
  );
  if (loading && !data) return <ListSkeleton />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data?.results.length) return <EmptyState />;
  return (
    <div className="card-grid">
      {data.results.map((exercise) => (
        <ManagementCard
          key={exercise.id}
          testId={`exercise-card-${exercise.id}`}
          title={exercise.name}
          description={exercise.description}
          viewHref={`${PATHS.catalog}/exercises/${exercise.id}`}
          editHref={`${PATHS.catalog}/exercises/${exercise.id}/edit`}
          onDelete={() =>
            void remove({
              name: exercise.name,
              remove: () => catalogApi.exercises.remove(exercise.id),
              onDone: reload,
            })
          }
        >
          <div className="row row--wrap">
            {exercise.muscleGroups.map((group) => (
              <IonChip key={group.id} color="tertiary">
                {t(`enums.muscleGroup.${group.slug}`, { defaultValue: group.name })}
              </IonChip>
            ))}
          </div>
        </ManagementCard>
      ))}
    </div>
  );
};

const PlansList = ({ search }: { search: string }) => {
  const { t } = useTranslation();
  const remove = useDeleteAction();
  const { data, error, loading, reload } = useResource(
    () => catalogApi.plans.list({ search }),
    [search],
  );
  if (loading && !data) return <ListSkeleton />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data?.results.length) return <EmptyState />;
  return (
    <div className="card-grid">
      {data.results.map((plan) => (
        <ManagementCard
          key={plan.id}
          testId={`plan-card-${plan.id}`}
          title={plan.name}
          description={plan.description}
          viewHref={`${PATHS.catalog}/plans/${plan.id}`}
          editHref={`${PATHS.catalog}/plans/${plan.id}/edit`}
          onDelete={() =>
            void remove({
              name: plan.name,
              remove: () => catalogApi.plans.remove(plan.id),
              onDone: reload,
            })
          }
        >
          <div className="row row--wrap">
            <IonChip>{t(`enums.goal.${plan.goal}`)}</IonChip>
            <IonChip>{t(`enums.difficulty.${plan.difficulty}`)}</IonChip>
            <IonChip>{t('catalog.workoutCount', { count: plan.workoutCount })}</IonChip>
          </div>
        </ManagementCard>
      ))}
    </div>
  );
};

/** Trainer catalog: workouts, exercises and training plans (sticky sub-tabs). */
const CatalogPage = () => {
  const { t } = useTranslation();
  const history = useHistory();
  const location = useLocation();
  const initial = queryParam(location.search, 'tab') as CatalogTab | null;
  const [tab, setTab] = useState<CatalogTab>(
    initial && TABS.includes(initial) ? initial : 'workouts',
  );
  const [search, setSearch] = useState('');
  const onSearch = useCallback((value: string) => setSearch(value), []);

  const changeTab = (next: CatalogTab) => {
    setTab(next);
    setSearch('');
    history.replace(`${PATHS.catalog}?tab=${next}`);
  };

  return (
    <PageLayout
      title={t('tabs.catalog')}
      subHeader={
        <IonSegment
          value={tab}
          onIonChange={(event) => changeTab(event.detail.value as CatalogTab)}
        >
          {TABS.map((key) => (
            <IonSegmentButton key={key} value={key} data-testid={`catalog-tab-${key}`}>
              <IonLabel>{t(`catalog.tabs.${key}`)}</IonLabel>
            </IonSegmentButton>
          ))}
        </IonSegment>
      }
      overlay={<AddFab href={`${PATHS.catalog}/${tab}/new`} label={t(`catalog.new.${tab}`)} />}
    >
      <SearchBox key={tab} onSearch={onSearch} />
      {tab === 'workouts' && <WorkoutsList search={search} />}
      {tab === 'exercises' && <ExercisesList search={search} />}
      {tab === 'plans' && <PlansList search={search} />}
    </PageLayout>
  );
};

export default CatalogPage;
