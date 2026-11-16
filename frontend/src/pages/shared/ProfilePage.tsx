import {
  IonAvatar,
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonNote,
  useIonRouter,
} from '@ionic/react';
import { createOutline, personCircleOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { progressApi } from '../../api/client-features';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { WeightChart } from '../../components/charts';
import { NotesEntry } from '../../components/notes/NotesEntry';
import { PageLayout } from '../../components/PageLayout';
import { PrivacyCard } from '../../components/privacy/PrivacyCard';
import { RemindersCard } from '../../components/profile/RemindersCard';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';

const Row = ({ label, value, testId }: { label: string; value: string; testId?: string }) => (
  <IonItem lines="full">
    <IonLabel>{label}</IonLabel>
    <IonNote slot="end" color="dark" data-testid={testId}>
      {value}
    </IonNote>
  </IonItem>
);

/** Profile (US-09): photo, personal data, goals, small weight chart, edit and logout. */
const ProfilePage = () => {
  const { t, i18n } = useTranslation();
  const router = useIonRouter();
  const { user, logout } = useAuth();
  const details = user?.details;
  const isClientWithDetails = user?.role === 'client' && Boolean(details);
  const weights = useResource(
    () => (isClientWithDetails ? progressApi.weights() : Promise.resolve(null)),
    [isClientWithDetails],
  );

  const onLogout = async () => {
    await logout();
    router.push(PATHS.login, 'root', 'replace');
  };

  if (!user) return null;
  const kg = (value: number | null | undefined) =>
    value === null || value === undefined
      ? '—'
      : `${formatNumber(value, i18n.language)} ${t('common.kg')}`;

  return (
    <PageLayout
      title={t('profile.title')}
      narrow
      actions={
        <IonButton
          routerLink={`${PATHS.profile}/edit`}
          className="icon-button"
          aria-label={t('profile.edit')}
          data-testid="profile-edit"
        >
          <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
        </IonButton>
      }
    >
      <div className="stack" style={{ alignItems: 'center', textAlign: 'center' }}>
        {user.profilePhotoUrl ? (
          <IonAvatar className="avatar-lg">
            <img src={user.profilePhotoUrl} alt={t('profile.photoAlt', { name: user.fullName })} />
          </IonAvatar>
        ) : (
          <IonIcon
            icon={personCircleOutline}
            style={{ fontSize: 96 }}
            color="medium"
            aria-hidden="true"
          />
        )}
        <h1 style={{ margin: 0 }} data-testid="profile-name">
          {user.fullName}
        </h1>
        <p className="muted" style={{ margin: 0 }}>
          {user.email}
        </p>
        {user.role !== 'client' && <p>{t(`enums.role.${user.role}`)}</p>}
      </div>

      <IonCard>
        <IonCardHeader>
          <IonCardTitle>{t('profile.personalInfo')}</IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          <IonList>
            <Row
              label={t('profile.age')}
              value={user.age !== null ? t('profile.years', { count: user.age }) : '—'}
            />
            {details && (
              <>
                <Row label={t('profile.height')} value={`${details.heightCm} cm`} />
                <Row label={t('profile.initialWeight')} value={kg(details.initialWeightKg)} />
                <Row
                  label={t('profile.currentWeight')}
                  value={kg(details.currentWeightKg)}
                  testId="profile-current-weight"
                />
              </>
            )}
          </IonList>
        </IonCardContent>
      </IonCard>

      {details && (
        <IonCard>
          <IonCardHeader>
            <IonCardTitle>{t('profile.goals')}</IonCardTitle>
          </IonCardHeader>
          <IonCardContent>
            <IonList>
              <Row
                label={t('profile.goal')}
                value={t(`enums.goal.${details.goal}`)}
                testId="profile-goal"
              />
              <Row
                label={t('profile.activityLevel')}
                value={t(`enums.activityLevel.${details.physicalActivityLevel}`)}
              />
              <Row
                label={t('profile.weeklyDays')}
                value={t('onboarding.daysOption', { count: details.weeklyTrainingDays })}
              />
            </IonList>
          </IonCardContent>
        </IonCard>
      )}

      {weights.data && weights.data.records.length > 0 && (
        <IonCard>
          <IonCardHeader>
            <IonCardTitle>{t('progress.weight')}</IonCardTitle>
          </IonCardHeader>
          <IonCardContent>
            <WeightChart summary={weights.data} compact />
          </IonCardContent>
        </IonCard>
      )}

      {user.role === 'client' && <NotesEntry />}
      {isClientWithDetails && <RemindersCard />}

      <PrivacyCard user={user} />

      <IonButton
        expand="block"
        color="danger"
        fill="outline"
        onClick={onLogout}
        data-testid="logout"
      >
        {t('common.logout')}
      </IonButton>
    </PageLayout>
  );
};

export default ProfilePage;
