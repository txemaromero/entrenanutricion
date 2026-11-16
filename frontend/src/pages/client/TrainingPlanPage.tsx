import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardSubtitle,
  IonCardTitle,
  IonChip,
  IonIcon,
  IonLabel,
  useIonToast,
} from '@ionic/react';
import { checkmarkCircle, flame, lockClosed, playCircle } from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router-dom';

import { progressApi, trainingApi } from '../../api/client-features';
import type { PlanWorkout } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { NotesEntry } from '../../components/notes/NotesEntry';
import { PageLayout } from '../../components/PageLayout';
import { ProgressRing } from '../../components/ProgressRing';
import { ErrorState, ListSkeleton } from '../../components/States';
import { TrainingDaysModal } from '../../components/training/TrainingDaysModal';
import { WeekStrip } from '../../components/training/WeekStrip';
import { useResource } from '../../hooks/useResource';
import { formatDate, toIsoDate, weekdayLabel, weekdayName } from '../../i18n/format';

const STATUS_ICON = { locked: lockClosed, available: playCircle, completed: checkmarkCircle };
const STATUS_COLOR = { locked: 'medium', available: 'primary', completed: 'success' };

/** Weekly plan (US-05): ordered workouts, scheduled day and lock state. */
const TrainingPlanPage = () => {
  const { t, i18n } = useTranslation();
  const history = useHistory();
  const [toast] = useIonToast();
  const { data: plan, error, loading, reload } = useResource(trainingApi.myPlan);
  // This week and the streak; the plan works without them (e.g. offline).
  const dashboard = useResource(() => progressApi.dashboard());
  const week = dashboard.data?.week;
  const scheduled = week?.filter((day) => day.scheduled).length ?? 0;
  const trained = Math.min(week?.filter((day) => day.completed).length ?? 0, scheduled);
  const streak = dashboard.data?.streakWeeks ?? 0;
  const refresh = () => Promise.all([reload(), dashboard.reload()]);
  // Each opening mounts a fresh picker with the current days.
  const [daysEditor, setDaysEditor] = useState(0);

  const open = (row: PlanWorkout) => {
    if (row.status === 'locked') {
      void toast({ message: t('errors.workout_locked'), duration: 2500, color: 'medium' });
      return;
    }
    history.push(`${PATHS.training}/workouts/${row.id}`);
  };

  return (
    <PageLayout title={t('tabs.training')} onRefresh={refresh}>
      {loading && !plan && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {plan && (
        <div className="stack">
          <NotesEntry onlyUnread />
          <IonCard data-testid="plan-progress">
            <IonCardContent>
              <div className="rings">
                <ProgressRing
                  testId="ring-plan"
                  ratio={plan.progress / 100}
                  label={t('training.summary.planLabel', {
                    progress: plan.progress,
                    cycle: plan.cycle,
                  })}
                  caption={
                    <>
                      {t('training.planProgress')}
                      <br />
                      {t('training.cycle', { cycle: plan.cycle })}
                    </>
                  }
                >
                  <strong>{plan.progress}%</strong>
                </ProgressRing>
                {week && scheduled > 0 && (
                  <ProgressRing
                    testId="ring-week"
                    ratio={trained / scheduled}
                    colorVar="--ion-color-tertiary"
                    label={t('training.summary.weekLabel', { done: trained, total: scheduled })}
                    caption={t('training.summary.week')}
                  >
                    <strong>
                      {trained}/{scheduled}
                    </strong>
                    <small>{t('training.summary.sessions')}</small>
                  </ProgressRing>
                )}
                {dashboard.data && (
                  <ProgressRing
                    testId="ring-streak"
                    ratio={streak > 0 ? 1 : 0}
                    colorVar="--en-streak"
                    label={t('training.summary.streakLabel', { count: streak })}
                    caption={t('training.summary.streak')}
                  >
                    <IonIcon icon={flame} className="ring__icon" />
                    <strong>{streak}</strong>
                    <small>{t('training.summary.weeks', { count: streak })}</small>
                  </ProgressRing>
                )}
              </div>
            </IonCardContent>
          </IonCard>

          <IonCard>
            {plan.plan.mediaUrl && plan.plan.mediaKind === 'image' && (
              <img
                src={plan.plan.mediaUrl}
                alt=""
                style={{ width: '100%', maxHeight: 200, objectFit: 'cover' }}
              />
            )}
            <IonCardHeader>
              <IonCardSubtitle>{t('training.myPlan')}</IonCardSubtitle>
              <IonCardTitle data-testid="plan-name">{plan.plan.name}</IonCardTitle>
            </IonCardHeader>
            <IonCardContent>
              <p>{plan.plan.description}</p>
              <div className="row row--wrap">
                <IonChip>{t(`enums.goal.${plan.plan.goal}`)}</IonChip>
                <IonChip>{t(`enums.difficulty.${plan.plan.difficulty}`)}</IonChip>
                <IonChip>{t('training.weeks', { count: plan.plan.durationWeeks })}</IonChip>
              </div>
            </IonCardContent>
          </IonCard>

          <h2 className="section-title">{t('training.thisWeek')}</h2>
          {week && <WeekStrip days={week} today={toIsoDate(new Date())} />}
          <div className="row row--between row--wrap" data-testid="training-days">
            <span>
              {t(plan.customTrainingDays ? 'training.days.custom' : 'training.days.default', {
                days: plan.trainingDays.map((day) => weekdayLabel(day, i18n.language)).join(', '),
              })}
            </span>
            <IonButton
              size="small"
              fill="outline"
              onClick={() => setDaysEditor((count) => count + 1)}
              data-testid="training-days-edit"
            >
              {t('training.days.change')}
            </IonButton>
          </div>
          {daysEditor > 0 && (
            <TrainingDaysModal
              key={daysEditor}
              isOpen
              days={plan.trainingDays}
              custom={plan.customTrainingDays}
              onClose={() => setDaysEditor(0)}
              onSaved={() => {
                setDaysEditor(0);
                void refresh();
              }}
            />
          )}
          <ol className="stack" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {plan.workouts.map((row) => (
              <li key={row.id}>
                <IonCard
                  button
                  onClick={() => open(row)}
                  aria-disabled={row.status === 'locked'}
                  data-testid={`plan-workout-${row.order}`}
                  data-status={row.status}
                >
                  <IonCardContent className="row" style={{ alignItems: 'flex-start' }}>
                    <IonIcon
                      icon={STATUS_ICON[row.status]}
                      color={STATUS_COLOR[row.status]}
                      style={{ fontSize: 32, flexShrink: 0 }}
                      aria-label={t(`enums.workoutStatus.${row.status}`)}
                    />
                    <div style={{ flex: 1 }}>
                      <h3 style={{ margin: 0, fontWeight: 600 }}>
                        {row.order}. {row.workout.name}
                      </h3>
                      <p className="muted" style={{ margin: '4px 0' }}>
                        {row.workout.description}
                      </p>
                      <IonLabel color="medium">
                        <small>
                          {row.status === 'completed' && row.completedAt
                            ? t('training.completedOn', {
                                date: formatDate(row.completedAt, i18n.language),
                              })
                            : row.scheduledDate
                              ? t('training.scheduledFor', {
                                  date: weekdayName(row.scheduledDate, i18n.language),
                                })
                              : ''}
                          {' · '}
                          {t('training.durationShort', {
                            minutes: row.summary.estimatedDurationMinutes,
                          })}
                        </small>
                      </IonLabel>
                    </div>
                  </IonCardContent>
                </IonCard>
              </li>
            ))}
          </ol>
        </div>
      )}
    </PageLayout>
  );
};

export default TrainingPlanPage;
