import { zodResolver } from '@hookform/resolvers/zod';
import { IonCard, IonCardContent, IonText, useIonRouter, useIonToast } from '@ionic/react';
import { useState } from 'react';
import { useForm, useWatch, type DefaultValues } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useLocation, useParams } from 'react-router-dom';

import { mealPlansApi } from '../../api/staff';
import type { MealPlan, MealPlanCategory } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { SelectField } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { FormActions, FormSection } from '../../components/staff/FormShell';
import { TranslationsSection } from '../../components/staff/TranslationsSection';
import { useFormInit } from '../../hooks/useFormInit';
import { useLeaveForm } from '../../hooks/useLeaveForm';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';
import { applyServerErrors, translateKey } from '../../utils/errors';
import { queryParam, returnToParam } from '../../utils/lists';
import { toNumber } from '../../utils/numbers';
import { caloriesMismatch, distributionSum, MEAL_KEYS, macrosKcal } from '../../utils/nutrition';
import { CATEGORIES, DIET_LABELS, mealPlanSchema, type MealPlanForm } from '../../validation/staff';
import { EMPTY_TRANSLATIONS, baseText, translationsForm } from '../../utils/translations';

const toForm = (plan: MealPlan): MealPlanForm => ({
  translations: translationsForm(plan.translations),
  name: baseText(plan, 'name', plan.name),
  category: plan.category,
  dietLabel: plan.dietLabel,
  calories: plan.calories,
  proteinsG: plan.proteinsG,
  carbsG: plan.carbsG,
  fatsG: plan.fatsG,
  description: baseText(plan, 'description', plan.description),
  mealDistribution: plan.mealDistribution,
});

/**
 * Create / edit a nutrition plan (US-25, US-26). Shows the kcal computed from the macros live
 * and warns when the declared kcal differ more than 10 %. With `?returnTo=` it goes back to
 * Assignments with the plan preselected.
 */
const MealPlanFormPage = () => {
  const { t, i18n } = useTranslation();
  const { id } = useParams<{ id?: string }>();
  const planId = id ? Number(id) : null;
  const location = useLocation();
  const returnTo = returnToParam(location.search);
  const category = queryParam(location.search, 'category') as MealPlanCategory | null;
  const router = useIonRouter();
  const leave = useLeaveForm(PATHS.mealPlans);
  const [toast] = useIonToast();
  const [saveError, setSaveError] = useState<unknown>();
  const existing = useResource(
    () => (planId ? mealPlansApi.get(planId) : Promise.resolve(null)),
    [planId],
  );

  const defaults: DefaultValues<MealPlanForm> = {
    translations: EMPTY_TRANSLATIONS,
    name: '',
    category: category && CATEGORIES.includes(category) ? category : undefined,
    description: '',
    mealDistribution: { breakfast: 20, lunch: 30, dinner: 30, snacks: 20 },
  };
  const { control, handleSubmit, reset, setError, formState } = useForm<MealPlanForm>({
    resolver: zodResolver(mealPlanSchema),
    defaultValues: defaults,
  });
  const values = useWatch({ control });

  useFormInit(existing.data, reset, toForm);

  const computed = macrosKcal(values.proteinsG, values.carbsG, values.fatsG);
  const mismatch = caloriesMismatch(values.calories, values.proteinsG, values.carbsG, values.fatsG);
  const sum = distributionSum(values.mealDistribution ?? {});
  const distributionError = translateKey(t, formState.errors.mealDistribution?.message);

  const onSubmit = handleSubmit(async (form) => {
    setSaveError(undefined);
    try {
      const saved = planId
        ? await mealPlansApi.update(planId, form)
        : await mealPlansApi.create(form);
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      if (returnTo) router.push(`${returnTo}?mealPlan=${saved.id}`, 'back', 'replace');
      else leave(planId ? undefined : `${PATHS.mealPlans}/${saved.id}`);
    } catch (error) {
      if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const loading = planId !== null && existing.loading && !existing.data;

  return (
    <PageLayout
      title={planId ? t('mealPlans.edit') : t('mealPlans.new')}
      backHref={returnTo ?? PATHS.mealPlans}
      narrow
    >
      {loading && <ListSkeleton />}
      {existing.error && <ErrorState error={existing.error} onRetry={existing.reload} />}
      {!loading && !existing.error && (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <TextField control={control} name="name" label={t('catalog.name')} required />
          <SelectField
            control={control}
            name="category"
            label={t('mealPlans.category')}
            required
            options={CATEGORIES.map((value) => ({
              value,
              label: t(`enums.mealPlanCategory.${value}`),
            }))}
          />
          <SelectField
            control={control}
            name="dietLabel"
            label={t('mealPlans.dietLabel')}
            required
            options={DIET_LABELS.map((value) => ({ value, label: t(`enums.dietLabel.${value}`) }))}
          />

          <FormSection title={t('mealPlans.energy')}>
            <TextField
              control={control}
              name="calories"
              label={t('mealPlans.calories')}
              type="number"
              inputMode="numeric"
              parse={toNumber}
              required
            />
            <TextField
              control={control}
              name="proteinsG"
              label={t('mealPlans.proteinsG')}
              type="number"
              inputMode="decimal"
              parse={toNumber}
              required
            />
            <TextField
              control={control}
              name="carbsG"
              label={t('mealPlans.carbsG')}
              type="number"
              inputMode="decimal"
              parse={toNumber}
              required
            />
            <TextField
              control={control}
              name="fatsG"
              label={t('mealPlans.fatsG')}
              type="number"
              inputMode="decimal"
              parse={toNumber}
              required
            />
            <IonCard>
              <IonCardContent data-testid="computed-kcal" data-mismatch={mismatch}>
                {t('mealPlans.computedKcal', { kcal: formatNumber(computed, i18n.language) })}
                {mismatch && (
                  <IonText color="warning" role="status">
                    <p style={{ margin: '4px 0 0' }}>{t('errors.calories_mismatch')}</p>
                  </IonText>
                )}
              </IonCardContent>
            </IonCard>
          </FormSection>

          <FormSection title={t('nutrition.mealSplit')}>
            <div className="card-grid" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
              {MEAL_KEYS.map((meal) => (
                <TextField
                  key={meal}
                  control={control}
                  name={`mealDistribution.${meal}`}
                  label={`${t(`enums.meal.${meal}`)} (%)`}
                  type="number"
                  inputMode="numeric"
                  parse={toNumber}
                  required
                />
              ))}
            </div>
            <IonText color={sum === 100 ? 'success' : 'danger'} role="status">
              <p style={{ margin: 0 }} data-testid="distribution-sum">
                {t('mealPlans.distributionTotal', { total: sum })}
              </p>
            </IonText>
            {distributionError && (
              <IonText color="danger" role="alert">
                <small>{distributionError}</small>
              </IonText>
            )}
          </FormSection>

          <TextField
            control={control}
            name="description"
            label={t('catalog.description')}
            helperText={t('common.optional')}
          />
          <TranslationsSection
            control={control}
            fields={[
              { key: 'name', label: t('catalog.name') },
              { key: 'description', label: t('catalog.description') },
            ]}
          />

          <FormActions
            onCancel={() => router.goBack()}
            saving={formState.isSubmitting}
            error={saveError}
          />
        </form>
      )}
    </PageLayout>
  );
};

export default MealPlanFormPage;
