import {
  IonButton,
  IonCard,
  IonCardContent,
  IonProgressBar,
  IonSegment,
  IonSegmentButton,
  IonLabel,
  IonText,
} from '@ionic/react';
import { useEffect, useRef, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router-dom';

import { meApi } from '../../api/me';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import {
  ChipMultiSelect,
  RadioField,
  SelectField,
  type Option,
} from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { errorMessage } from '../../utils/errors';
import {
  ACTIVITY_LEVELS,
  DAILY_TIMES,
  DIET_TYPES,
  EQUIPMENT,
  EXERCISE_TYPES,
  FOOD_RESTRICTIONS,
  GOALS,
  MACRO_ASSESSMENTS,
  MEDICAL_CONDITIONS,
  ONBOARDING_DEFAULTS,
  ONBOARDING_STEPS,
  SUPPLEMENTS,
  TRAINING_PREFERENCES,
  toOnboardingPayload,
  validateStep,
  type OnboardingForm,
} from '../../validation/onboarding';
import { toNumber } from '../../utils/numbers';

const OnboardingPage = () => {
  const { t } = useTranslation();
  const history = useHistory();
  const { refreshUser } = useAuth();
  const [step, setStep] = useState(0);
  const [attempted, setAttempted] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>();
  const [submitting, setSubmitting] = useState(false);
  const contentRef = useRef<HTMLIonContentElement>(null);

  const { control, getValues, setError, clearErrors } = useForm<OnboardingForm>({
    defaultValues: ONBOARDING_DEFAULTS,
  });
  const values = useWatch({ control }) as OnboardingForm;
  const total = ONBOARDING_STEPS.length;

  const options = (group: string, list: readonly string[]): Option[] =>
    list.map((value) => ({ value, label: t(`enums.${group}.${value}`) }));

  const applyValidation = (current: OnboardingForm) => {
    const issues = validateStep(step, current);
    clearErrors();
    Object.entries(issues).forEach(([field, message]) =>
      setError(field as keyof OnboardingForm, { type: 'validate', message }),
    );
    return Object.keys(issues).length === 0;
  };

  // After a failed attempt, errors update live while the user fixes the step.
  useEffect(() => {
    if (attempted) applyValidation(values);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- revalidate on every change
  }, [values, attempted]);

  const goTo = (next: number) => {
    setAttempted(false);
    clearErrors();
    setStep(next);
    void contentRef.current?.scrollToTop(0);
  };

  const next = async () => {
    setAttempted(true);
    if (!applyValidation(getValues())) return;
    if (step < total - 1) {
      goTo(step + 1);
      return;
    }
    setSubmitting(true);
    setSubmitError(undefined);
    try {
      await meApi.submitOnboarding(toOnboardingPayload(getValues()));
      await refreshUser();
      history.replace(PATHS.status);
    } catch (error) {
      setSubmitError(error);
    } finally {
      setSubmitting(false);
    }
  };

  const stepKey = ONBOARDING_STEPS[step].key;
  const needsRestrictionText = (values.foodRestrictions ?? []).some((item) => item !== 'none');

  return (
    <PageLayout title={t('onboarding.title')} narrow ref={contentRef}>
      <div className="stack">
        <div>
          <IonText color="medium">
            <p data-testid="onboarding-step">
              {t('onboarding.stepOf', { current: step + 1, total })}
            </p>
          </IonText>
          <IonProgressBar
            value={(step + 1) / total}
            aria-label={t('onboarding.progress')}
            aria-valuenow={step + 1}
            aria-valuemin={1}
            aria-valuemax={total}
          />
        </div>
        <h2 style={{ margin: 0 }}>{t(`onboarding.steps.${stepKey}`)}</h2>
        <IonCard>
          <IonCardContent className="stack">
            {stepKey === 'personal' && (
              <>
                <TextField
                  control={control}
                  name="heightCm"
                  label={t('onboarding.heightCm')}
                  type="number"
                  inputMode="numeric"
                  required
                  parse={toNumber}
                  helperText={t('onboarding.heightHelp')}
                />
                <TextField
                  control={control}
                  name="initialWeightKg"
                  label={t('onboarding.weightKg')}
                  type="number"
                  inputMode="decimal"
                  required
                  parse={toNumber}
                  helperText={t('onboarding.weightHelp')}
                />
              </>
            )}

            {stepKey === 'goals' && (
              <>
                <RadioField
                  control={control}
                  name="goal"
                  label={t('onboarding.goal')}
                  required
                  options={options('goal', GOALS)}
                />
                <SelectField
                  control={control}
                  name="weeklyTrainingDays"
                  label={t('onboarding.weeklyTrainingDays')}
                  required
                  options={[1, 2, 3, 4, 5, 6].map((value) => ({
                    value,
                    label: t('onboarding.daysOption', { count: value }),
                  }))}
                />
                <SelectField
                  control={control}
                  name="dailyTrainingTime"
                  label={t('onboarding.dailyTrainingTime')}
                  required
                  options={options('dailyTrainingTime', DAILY_TIMES)}
                />
                {values.goal && values.goal !== 'maintain' && (
                  <div className="stack">
                    <TextField
                      control={control}
                      name="targetChange"
                      label={t(
                        values.goal === 'lose_weight'
                          ? 'onboarding.targetLose'
                          : 'onboarding.targetGain',
                      )}
                      type="number"
                      inputMode="decimal"
                      required
                      parse={toNumber}
                    />
                    <Controller
                      control={control}
                      name="targetUnit"
                      render={({ field }) => (
                        <IonSegment
                          value={field.value}
                          onIonChange={(event) => field.onChange(event.detail.value)}
                          aria-label={t('onboarding.unit')}
                          data-testid="field-targetUnit"
                        >
                          <IonSegmentButton value="kg">
                            <IonLabel>kg</IonLabel>
                          </IonSegmentButton>
                          <IonSegmentButton value="lbs">
                            <IonLabel>lbs</IonLabel>
                          </IonSegmentButton>
                        </IonSegment>
                      )}
                    />
                  </div>
                )}
              </>
            )}

            {stepKey === 'activity' && (
              <>
                <RadioField
                  control={control}
                  name="physicalActivityLevel"
                  label={t('onboarding.activityLevel')}
                  required
                  options={options('activityLevel', ACTIVITY_LEVELS)}
                />
                <ChipMultiSelect
                  control={control}
                  name="usualExerciseTypes"
                  label={t('onboarding.exerciseTypes')}
                  required
                  options={options('exerciseType', EXERCISE_TYPES)}
                />
                <ChipMultiSelect
                  control={control}
                  name="availableEquipment"
                  label={t('onboarding.equipment')}
                  required
                  exclusive={['no_equipment']}
                  options={options('equipment', EQUIPMENT)}
                />
              </>
            )}

            {stepKey === 'diet' && (
              <>
                <SelectField
                  control={control}
                  name="dietType"
                  label={t('onboarding.dietType')}
                  required
                  options={options('dietType', DIET_TYPES)}
                />
                <ChipMultiSelect
                  control={control}
                  name="foodRestrictions"
                  label={t('onboarding.restrictions')}
                  required
                  exclusive={['none']}
                  options={options('foodRestriction', FOOD_RESTRICTIONS)}
                />
                {needsRestrictionText && (
                  <TextField
                    control={control}
                    name="customFoodRestrictions"
                    label={t('onboarding.restrictionsText')}
                    required
                  />
                )}
                <TextField
                  control={control}
                  name="mealsPerDay"
                  label={t('onboarding.mealsPerDay')}
                  type="number"
                  inputMode="numeric"
                  required
                  parse={toNumber}
                />
                <SelectField
                  control={control}
                  name="macronutrientIntakeSelfAssessment"
                  label={t('onboarding.macroAssessment')}
                  required
                  options={options('macroSelfAssessment', MACRO_ASSESSMENTS)}
                />
              </>
            )}

            {stepKey === 'health' && (
              <>
                <ChipMultiSelect
                  control={control}
                  name="medicalConditions"
                  label={t('onboarding.medicalConditions')}
                  required
                  exclusive={['none']}
                  options={options('medicalCondition', MEDICAL_CONDITIONS)}
                />
                {(values.medicalConditions ?? []).includes('other') && (
                  <TextField
                    control={control}
                    name="customMedicalCondition"
                    label={t('onboarding.medicalText')}
                    required
                  />
                )}
                <ChipMultiSelect
                  control={control}
                  name="supplements"
                  label={t('onboarding.supplements')}
                  required
                  exclusive={['none']}
                  options={options('supplement', SUPPLEMENTS)}
                />
              </>
            )}

            {stepKey === 'preferences' && (
              <>
                <RadioField
                  control={control}
                  name="trainingPreference"
                  label={t('onboarding.trainingPreference')}
                  required
                  options={options('trainingPreference', TRAINING_PREFERENCES)}
                />
                <TextField
                  control={control}
                  name="preferencesText"
                  label={t('onboarding.preferencesText')}
                  helperText={t('common.optional')}
                />
              </>
            )}
          </IonCardContent>
        </IonCard>

        {Boolean(submitError) && (
          <IonText color="danger" role="alert">
            <p>{errorMessage(t, submitError)}</p>
          </IonText>
        )}
        <div className="form-actions">
          {step > 0 && (
            <IonButton
              fill="outline"
              color="medium"
              onClick={() => goTo(step - 1)}
              data-testid="onboarding-back"
            >
              {t('common.previous')}
            </IonButton>
          )}
          <IonButton
            onClick={() => void next()}
            disabled={submitting}
            data-testid="onboarding-next"
          >
            {step === total - 1 ? t('onboarding.submit') : t('common.next')}
          </IonButton>
        </div>
      </div>
    </PageLayout>
  );
};

export default OnboardingPage;
