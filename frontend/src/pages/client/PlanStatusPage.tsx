import {
  IonCard,
  IonCardContent,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonSpinner,
  useIonViewWillEnter,
} from '@ionic/react';
import { checkmarkCircle, closeCircle } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { useAuth } from '../../auth/useAuth';
import { NotesEntry } from '../../components/notes/NotesEntry';
import { PageLayout } from '../../components/PageLayout';

const StatusRow = ({ label, done, testId }: { label: string; done: boolean; testId: string }) => {
  const { t } = useTranslation();
  return (
    <IonItem lines="none" data-testid={testId} data-done={done}>
      <IonIcon
        slot="start"
        icon={done ? checkmarkCircle : closeCircle}
        color={done ? 'success' : 'danger'}
        aria-hidden="true"
      />
      <IonLabel>{label}</IonLabel>
      <span className="status-dot">
        {done ? t('planStatus.assigned') : t('planStatus.pending')}
      </span>
    </IonItem>
  );
};

/** Waiting screen for clients without both plans; refreshes on enter and on pull. */
const PlanStatusPage = () => {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();

  useIonViewWillEnter(() => {
    void refreshUser().catch(() => undefined);
  });

  if (!user) return null;
  return (
    <PageLayout title={t('tabs.status')} onRefresh={refreshUser} narrow>
      <div className="stack" style={{ textAlign: 'center', alignItems: 'center' }}>
        <IonSpinner name="dots" color="primary" aria-hidden="true" />
        <h2 data-testid="plan-status-title">{t('planStatus.preparing')}</h2>
        <p className="muted">{t('planStatus.explanation')}</p>
      </div>
      <IonCard>
        <IonCardContent>
          <IonList>
            <StatusRow
              label={t('planStatus.training')}
              done={user.hasTrainingPlan}
              testId="status-training"
            />
            <StatusRow
              label={t('planStatus.nutrition')}
              done={user.hasNutritionPlan}
              testId="status-nutrition"
            />
          </IonList>
        </IonCardContent>
      </IonCard>
      <p className="muted" style={{ textAlign: 'center' }}>
        {t('planStatus.pullToRefresh')}
      </p>
      {user.onboardingCompleted && <NotesEntry />}
    </PageLayout>
  );
};

export default PlanStatusPage;
