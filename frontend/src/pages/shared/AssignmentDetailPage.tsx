import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonIcon,
  IonSelect,
  IonSelectOption,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { addCircleOutline, personAddOutline } from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation, useParams } from 'react-router-dom';

import { ApiError } from '../../api/errors';
import { assignmentsApi, catalogApi, mealPlansApi, usersApi } from '../../api/staff';
import type { PlanRef } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { OnboardingAnswers, UserOverview } from '../../components/staff/UserProfileBlocks';
import { useConfirm } from '../../hooks/useConfirm';
import { useResource } from '../../hooks/useResource';
import { errorMessage } from '../../utils/errors';
import { queryParam } from '../../utils/lists';

type Kind = 'training' | 'nutrition';

interface AssignBoxProps {
  kind: Kind;
  userName: string;
  current: PlanRef | null;
  plans: PlanRef[];
  preselected?: number;
  createHref: string;
  onAssign: (planId: number, replace: boolean) => Promise<void>;
}

const AssignBox = ({
  kind,
  userName,
  current,
  plans,
  preselected,
  createHref,
  onAssign,
}: AssignBoxProps) => {
  const { t } = useTranslation();
  const router = useIonRouter();
  const confirm = useConfirm();
  // The parent re-mounts this box (key) when a newly created plan comes preselected.
  const [selected, setSelected] = useState<number | undefined>(preselected);
  const [busy, setBusy] = useState(false);

  const planName = (id: number) => plans.find((plan) => plan.id === id)?.name ?? '';

  const assign = async () => {
    if (!selected) return;
    const accepted = current
      ? await confirm({
          header: t('assignments.replaceTitle'),
          message: t('assignments.replaceMessage', { current: current.name }),
          confirmText: t('assignments.replace'),
        })
      : await confirm({
          header: t('assignments.confirmTitle'),
          message: t('assignments.confirmMessage', { plan: planName(selected), user: userName }),
          confirmText: t('common.assign'),
        });
    if (!accepted) return;
    setBusy(true);
    try {
      await onAssign(selected, Boolean(current));
    } finally {
      setBusy(false);
    }
  };

  return (
    <IonCard data-testid={`assign-${kind}`}>
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.05rem' }}>{t(`assignments.${kind}Title`)}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        <p style={{ margin: 0 }}>
          {current ? t('assignments.currentPlan', { plan: current.name }) : t('assignments.noPlan')}
        </p>
        <IonSelect
          label={t('assignments.choosePlan')}
          labelPlacement="floating"
          fill="outline"
          interface="popover"
          value={selected}
          onIonChange={(event) => setSelected(event.detail.value)}
          data-testid={`select-${kind}-plan`}
        >
          {plans.map((plan) => (
            <IonSelectOption key={plan.id} value={plan.id}>
              {plan.name}
            </IonSelectOption>
          ))}
        </IonSelect>
        <div className="row row--wrap">
          <IonButton
            fill="outline"
            onClick={() => router.push(createHref)}
            data-testid={`create-${kind}-plan`}
          >
            <IonIcon slot="start" icon={addCircleOutline} aria-hidden="true" />
            {t('assignments.createPlan')}
          </IonButton>
          <IonButton
            color="tertiary"
            disabled={!selected || busy}
            onClick={() => void assign()}
            data-testid={`assign-${kind}-button`}
          >
            <IonIcon slot="start" icon={personAddOutline} aria-hidden="true" />
            {t('common.assign')}
          </IonButton>
        </div>
      </IonCardContent>
    </IonCard>
  );
};

/** Client file for assigning plans: data, relevant answers, weight history and selectors. */
const AssignmentDetailPage = () => {
  const { t } = useTranslation();
  const userId = Number(useParams<{ userId: string }>().userId);
  const location = useLocation();
  const router = useIonRouter();
  const [toast] = useIonToast();
  const confirm = useConfirm();
  const { user: me } = useAuth();
  const canTraining = me?.role === 'trainer' || me?.role === 'admin';
  const canNutrition = me?.role === 'nutritionist' || me?.role === 'admin';

  const client = useResource(() => usersApi.get(userId), [userId]);
  const trainingPlans = useResource(() =>
    canTraining ? catalogApi.plans.list({ limit: 100 }) : Promise.resolve(null),
  );
  const mealPlans = useResource(() =>
    canNutrition ? mealPlansApi.list({ limit: 100 }) : Promise.resolve(null),
  );

  const preselectedTraining = Number(queryParam(location.search, 'trainingPlan')) || undefined;
  const preselectedMeal = Number(queryParam(location.search, 'mealPlan')) || undefined;
  const here = `${PATHS.assignments}/${userId}`;

  const run = async (kind: Kind, planId: number, replace: boolean) => {
    const call =
      kind === 'training' ? assignmentsApi.assignTraining : assignmentsApi.assignNutrition;
    try {
      await call(userId, planId, replace);
    } catch (error) {
      // Regression #9: a plan assigned meanwhile gives a specific 409 → ask to replace it.
      if (error instanceof ApiError && error.code.endsWith('_plan_already_assigned') && !replace) {
        const current = (error.extra.currentPlan as PlanRef | undefined)?.name ?? '';
        const accepted = await confirm({
          header: t('assignments.replaceTitle'),
          message: t('assignments.replaceMessage', { current }),
          confirmText: t('assignments.replace'),
        });
        if (!accepted) return;
        await call(userId, planId, true);
      } else {
        void toast({ message: errorMessage(t, error), duration: 3500, color: 'danger' });
        return;
      }
    }
    void toast({ message: t('assignments.assigned'), duration: 2000, color: 'success' });
    const updated = await client.reload();
    // Back to the list once nothing is left for this role (the client leaves the pending list).
    const pendingForMe =
      updated &&
      ((canTraining && !updated.trainingAssignment) ||
        (canNutrition && !updated.nutritionAssignment));
    if (!pendingForMe) router.push(PATHS.assignments, 'back', 'replace');
  };

  const data = client.data;
  const sections =
    me?.role === 'trainer'
      ? (['training', 'health', 'preferences'] as const)
      : me?.role === 'nutritionist'
        ? (['nutrition', 'health'] as const)
        : (['training', 'nutrition', 'health', 'preferences'] as const);

  return (
    <PageLayout title={data?.fullName ?? t('tabs.assignments')} backHref={PATHS.assignments}>
      {client.loading && !data && <ListSkeleton />}
      {client.error && <ErrorState error={client.error} onRetry={client.reload} />}
      {data && (
        <div className="stack" data-testid="assignment-detail">
          {canTraining && (
            <AssignBox
              key={`training-${preselectedTraining ?? ''}`}
              kind="training"
              userName={data.fullName}
              current={data.trainingAssignment?.plan ?? null}
              plans={(trainingPlans.data?.results ?? []).map(({ id, name }) => ({ id, name }))}
              preselected={preselectedTraining}
              createHref={`${PATHS.catalog}/plans/new?returnTo=${encodeURIComponent(here)}`}
              onAssign={(planId, replace) => run('training', planId, replace)}
            />
          )}
          {canNutrition && (
            <AssignBox
              key={`nutrition-${preselectedMeal ?? ''}`}
              kind="nutrition"
              userName={data.fullName}
              current={data.nutritionAssignment?.plan ?? null}
              plans={(mealPlans.data?.results ?? []).map(({ id, name }) => ({ id, name }))}
              preselected={preselectedMeal}
              createHref={`${PATHS.mealPlans}/new?returnTo=${encodeURIComponent(here)}`}
              onAssign={(planId, replace) => run('nutrition', planId, replace)}
            />
          )}
          <UserOverview user={data} />
          {data.onboarding && (
            <OnboardingAnswers onboarding={data.onboarding} sections={[...sections]} />
          )}
        </div>
      )}
    </PageLayout>
  );
};

export default AssignmentDetailPage;
