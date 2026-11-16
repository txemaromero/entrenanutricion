import { IonButton, IonIcon } from '@ionic/react';
import { createOutline, personAddOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { usersApi } from '../../api/staff';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { ClientNotesCard } from '../../components/notes/StaffNotes';
import { ClientDiaryCard } from '../../components/nutrition/DiarySummaryCard';
import { ClientAdherenceCard } from '../../components/staff/Adherence';
import { OnboardingAnswers, UserOverview } from '../../components/staff/UserProfileBlocks';
import { useResource } from '../../hooks/useResource';

/** Full user profile for staff: data, goals, health, preferences, plans and progress. */
const UserDetailPage = () => {
  const { t } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { user: me } = useAuth();
  const { data, error, loading, reload } = useResource(() => usersApi.get(id), [id]);

  return (
    <PageLayout
      title={data?.fullName ?? t('tabs.users')}
      backHref={PATHS.users}
      onRefresh={reload}
      actions={
        me?.role === 'admin' && (
          <IonButton
            routerLink={`${PATHS.users}/${id}/edit`}
            className="icon-button"
            aria-label={t('common.edit')}
            data-testid="detail-edit"
          >
            <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
          </IonButton>
        )
      }
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="user-detail">
          <UserOverview user={data} />
          {data.role === 'client' && data.trainingPlan && <ClientAdherenceCard userId={data.id} />}
          {data.role === 'client' && data.onboarding && (
            <IonButton
              color="tertiary"
              routerLink={`${PATHS.assignments}/${data.id}`}
              data-testid="assign-from-detail"
            >
              <IonIcon slot="start" icon={personAddOutline} aria-hidden="true" />
              {t('common.assign')}
            </IonButton>
          )}
          {data.role === 'client' && data.nutritionPlan && <ClientDiaryCard userId={data.id} />}
          {data.role === 'client' && <ClientNotesCard userId={data.id} />}
          {data.onboarding && <OnboardingAnswers onboarding={data.onboarding} />}
        </div>
      )}
    </PageLayout>
  );
};

export default UserDetailPage;
