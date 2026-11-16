import {
  IonAvatar,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonChip,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonNote,
} from '@ionic/react';
import { personCircleOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import type { Onboarding, UserDetail, UserSummary } from '../../api/types';
import { formatDate, formatNumber, weekdayLabel } from '../../i18n/format';
import { WeightChart } from '../charts';

const AVATAR_COLORS = 6;

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();

/** The photo, or the initials on a colour of the theme that stays the same for each person. */
export const Avatar = ({
  user,
  size = 48,
}: {
  user: Pick<UserSummary, 'profilePhotoUrl'> & { fullName?: string; id?: number };
  size?: number;
}) => {
  if (user.profilePhotoUrl) {
    return (
      <IonAvatar style={{ width: size, height: size, flexShrink: 0 }}>
        <img src={user.profilePhotoUrl} alt="" />
      </IonAvatar>
    );
  }
  const initials = user.fullName ? initialsOf(user.fullName) : '';
  if (!initials) {
    return (
      <IonIcon
        icon={personCircleOutline}
        style={{ fontSize: size, flexShrink: 0 }}
        color="medium"
        aria-hidden="true"
      />
    );
  }
  const seed =
    user.id ?? [...(user.fullName ?? '')].reduce((sum, letter) => sum + letter.charCodeAt(0), 0);
  return (
    <span
      className="avatar-initials"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.38,
        background: `var(--en-avatar-${(seed % AVATAR_COLORS) + 1})`,
      }}
      aria-hidden="true"
      data-testid="avatar-initials"
    >
      {initials}
    </span>
  );
};

/** Chips with the current training / nutrition plans of a user (or what is missing). */
export const PlanChips = ({ user }: { user: UserSummary }) => {
  const { t } = useTranslation();
  if (user.role !== 'client') return null;
  return (
    <div className="row row--wrap">
      <IonChip color={user.trainingPlan ? 'primary' : 'medium'} outline={!user.trainingPlan}>
        {user.trainingPlan ? user.trainingPlan.name : t('enums.missing.training')}
      </IonChip>
      <IonChip color={user.nutritionPlan ? 'primary' : 'medium'} outline={!user.nutritionPlan}>
        {user.nutritionPlan ? user.nutritionPlan.name : t('enums.missing.nutrition')}
      </IonChip>
    </div>
  );
};

const Row = ({ label, value }: { label: string; value: string }) => (
  <IonItem lines="full">
    <IonLabel className="ion-text-wrap">{label}</IonLabel>
    <IonNote
      slot="end"
      color="dark"
      className="ion-text-wrap"
      style={{ maxWidth: '55%', textAlign: 'right' }}
    >
      {value}
    </IonNote>
  </IonItem>
);

const Card = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <IonCard>
    <IonCardHeader>
      <IonCardTitle style={{ fontSize: '1.05rem' }}>{title}</IonCardTitle>
    </IonCardHeader>
    <IonCardContent>{children}</IonCardContent>
  </IonCard>
);

type Section = 'training' | 'nutrition' | 'health' | 'preferences';

/** Onboarding answers grouped by topic; `sections` limits what a role needs to see. */
export const OnboardingAnswers = ({
  onboarding,
  sections = ['training', 'nutrition', 'health', 'preferences'],
}: {
  onboarding: Onboarding;
  sections?: Section[];
}) => {
  const { t, i18n } = useTranslation();
  const list = (group: string, values: string[]) =>
    values.map((value) => t(`enums.${group}.${value}`)).join(', ');
  const withText = (text: string, extra: string) => (extra ? `${text} (${extra})` : text);

  return (
    <>
      {sections.includes('training') && (
        <Card title={t('users.sections.training')}>
          <IonList>
            <Row label={t('profile.goal')} value={t(`enums.goal.${onboarding.goal}`)} />
            <Row
              label={t('onboarding.weeklyTrainingDays')}
              value={String(onboarding.weeklyTrainingDays)}
            />
            {Boolean(onboarding.trainingDays?.length) && (
              <Row
                label={t('training.days.chosenByClient')}
                value={(onboarding.trainingDays ?? [])
                  .map((day) => weekdayLabel(day, i18n.language))
                  .join(', ')}
              />
            )}
            <Row
              label={t('onboarding.dailyTrainingTime')}
              value={t(`enums.dailyTrainingTime.${onboarding.dailyTrainingTime}`)}
            />
            <Row
              label={t('onboarding.activityLevel')}
              value={t(`enums.activityLevel.${onboarding.physicalActivityLevel}`)}
            />
            <Row
              label={t('onboarding.exerciseTypes')}
              value={list('exerciseType', onboarding.usualExerciseTypes)}
            />
            <Row
              label={t('onboarding.equipment')}
              value={list('equipment', onboarding.availableEquipment)}
            />
            <Row
              label={t('onboarding.trainingPreference')}
              value={t(`enums.trainingPreference.${onboarding.trainingPreference}`)}
            />
          </IonList>
        </Card>
      )}
      {sections.includes('nutrition') && (
        <Card title={t('users.sections.nutrition')}>
          <IonList>
            <Row
              label={t('onboarding.dietType')}
              value={t(`enums.dietType.${onboarding.diet.dietType}`)}
            />
            <Row
              label={t('onboarding.restrictions')}
              value={withText(
                list('foodRestriction', onboarding.diet.foodRestrictions),
                onboarding.diet.customFoodRestrictions,
              )}
            />
            <Row label={t('onboarding.mealsPerDay')} value={String(onboarding.diet.mealsPerDay)} />
            <Row
              label={t('onboarding.macroAssessment')}
              value={t(
                `enums.macroSelfAssessment.${onboarding.diet.macronutrientIntakeSelfAssessment}`,
              )}
            />
          </IonList>
        </Card>
      )}
      {sections.includes('health') && (
        <Card title={t('users.sections.health')}>
          <IonList>
            <Row
              label={t('onboarding.medicalConditions')}
              value={withText(
                list('medicalCondition', onboarding.health.medicalConditions),
                onboarding.health.customMedicalCondition,
              )}
            />
            <Row
              label={t('onboarding.supplements')}
              value={list('supplement', onboarding.health.supplements)}
            />
          </IonList>
        </Card>
      )}
      {sections.includes('preferences') && onboarding.preferencesText && (
        <Card title={t('onboarding.steps.preferences')}>
          <p style={{ margin: 0 }}>{onboarding.preferencesText}</p>
        </Card>
      )}
    </>
  );
};

/** Personal data, weight history chart and current plans of a user. */
export const UserOverview = ({ user }: { user: UserDetail }) => {
  const { t, i18n } = useTranslation();
  const kg = (value?: number | null) =>
    value === null || value === undefined
      ? '—'
      : `${formatNumber(value, i18n.language)} ${t('common.kg')}`;
  const details = user.details;

  return (
    <>
      <div className="row" style={{ gap: 16 }}>
        <Avatar user={user} size={72} />
        <div>
          <h1 style={{ margin: 0 }} data-testid="user-name">
            {user.fullName}
          </h1>
          <p className="muted" style={{ margin: 0 }}>
            {user.email}
          </p>
          <div className="row row--wrap">
            <IonChip>{t(`enums.role.${user.role}`)}</IonChip>
            <IonChip color="medium">{t(`enums.userStatus.${user.status}`)}</IonChip>
          </div>
        </div>
      </div>
      <Card title={t('profile.personalInfo')}>
        <IonList>
          <Row
            label={t('profile.age')}
            value={user.age !== null ? t('profile.years', { count: user.age }) : '—'}
          />
          <Row
            label={t('auth.register.gender')}
            value={user.gender ? t(`enums.gender.${user.gender}`) : '—'}
          />
          <Row label={t('users.joined')} value={formatDate(user.dateJoined, i18n.language)} />
          {details && (
            <>
              <Row label={t('profile.height')} value={`${details.heightCm} cm`} />
              <Row label={t('profile.initialWeight')} value={kg(details.initialWeightKg)} />
              <Row label={t('profile.currentWeight')} value={kg(details.currentWeightKg)} />
              <Row label={t('progress.targetWeight')} value={kg(details.targetWeightKg)} />
            </>
          )}
        </IonList>
      </Card>
      {user.role === 'client' && (
        <Card title={t('users.currentPlans')}>
          <IonList>
            <Row
              label={t('planStatus.training')}
              value={
                user.trainingAssignment
                  ? `${user.trainingAssignment.plan.name} · ${t('training.cycle', { cycle: user.trainingAssignment.cycle })} · ${user.trainingAssignment.progress}%`
                  : t('planStatus.pending')
              }
            />
            <Row
              label={t('planStatus.nutrition')}
              value={
                user.nutritionAssignment
                  ? user.nutritionAssignment.plan.name
                  : t('planStatus.pending')
              }
            />
          </IonList>
        </Card>
      )}
      {details && user.weightRecords.length > 0 && (
        <Card title={t('users.weightHistory')}>
          <WeightChart
            summary={{
              goal: details.goal,
              initialWeightKg: details.initialWeightKg,
              targetWeightKg: details.targetWeightKg,
              currentWeightKg: details.currentWeightKg,
              records: user.weightRecords,
            }}
            compact
          />
        </Card>
      )}
    </>
  );
};
