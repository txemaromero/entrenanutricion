import { zodResolver } from '@hookform/resolvers/zod';
import { IonText, useIonRouter, useIonToast } from '@ionic/react';
import { useState } from 'react';
import { useForm, type DefaultValues } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { foodsApi } from '../../api/foods';
import type { Food, FoodInput } from '../../api/types';
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
import { applyServerErrors } from '../../utils/errors';
import {
  FOOD_CATEGORIES,
  MICRONUTRIENTS,
  OPTIONAL_NUTRIENTS,
  OTHER_NUTRIENTS,
  type NutrientKey,
} from '../../utils/foods';
import { toNumber } from '../../utils/numbers';
import { foodSchema, type FoodForm } from '../../validation/staff';
import { EMPTY_TRANSLATIONS, baseText, translationsForm } from '../../utils/translations';

const toForm = (food: Food): FoodForm => ({
  translations: translationsForm(food.translations),
  name: baseText(food, 'name', food.name),
  category: food.category,
  calories: food.calories,
  proteinsG: food.proteinsG,
  carbsG: food.carbsG,
  fatsG: food.fatsG,
  ...Object.fromEntries(OPTIONAL_NUTRIENTS.map((key) => [key, food[key]])),
});

/** Empty optional fields are sent as null so an edit can also clear a value. */
const toInput = (form: FoodForm): FoodInput =>
  ({
    ...form,
    ...Object.fromEntries(OPTIONAL_NUTRIENTS.map((key) => [key, form[key] ?? null])),
  }) as FoodInput;

/** Create / edit a food of the library (values per 100 g). */
const FoodFormPage = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id?: string }>();
  const foodId = id ? Number(id) : null;
  const router = useIonRouter();
  const leave = useLeaveForm(PATHS.foods);
  const [toast] = useIonToast();
  const [saveError, setSaveError] = useState<unknown>();
  const existing = useResource(
    () => (foodId ? foodsApi.get(foodId) : Promise.resolve(null)),
    [foodId],
  );
  const defaults: DefaultValues<FoodForm> = { name: '', translations: EMPTY_TRANSLATIONS };
  const { control, handleSubmit, reset, setError, formState } = useForm<FoodForm>({
    resolver: zodResolver(foodSchema),
    defaultValues: defaults,
  });

  useFormInit(existing.data, reset, toForm);

  const onSubmit = handleSubmit(async (form) => {
    setSaveError(undefined);
    try {
      const saved = foodId
        ? await foodsApi.update(foodId, toInput(form))
        : await foodsApi.create(toInput(form));
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      leave(foodId ? undefined : `${PATHS.foods}/${saved.id}`);
    } catch (error) {
      if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const numberField = (name: keyof FoodForm, label: string, required = false) => (
    <TextField
      key={name}
      control={control}
      name={name}
      label={label}
      type="number"
      inputMode="decimal"
      parse={toNumber}
      required={required}
    />
  );
  const nutrientFields = (nutrients: [NutrientKey, string][]) => (
    <div className="card-grid" style={{ gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
      {nutrients.map(([key, unit]) => numberField(key, `${t(`foods.nutrients.${key}`)} (${unit})`))}
    </div>
  );
  const loading = foodId !== null && existing.loading && !existing.data;

  return (
    <PageLayout
      title={foodId ? t('foods.edit') : t('foods.new')}
      backHref={foodId ? `${PATHS.foods}/${foodId}` : PATHS.foods}
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
            label={t('foods.category')}
            required
            options={FOOD_CATEGORIES.map((value) => ({
              value,
              label: t(`enums.foodCategory.${value}`),
            }))}
          />
          <FormSection title={t('foods.macrosPer100g')}>
            {numberField('calories', t('foods.calories'), true)}
            {numberField('proteinsG', t('mealPlans.proteinsG'), true)}
            {numberField('carbsG', t('mealPlans.carbsG'), true)}
            {numberField('fatsG', t('mealPlans.fatsG'), true)}
          </FormSection>
          <FormSection title={t('foods.otherNutrients')}>
            <IonText color="medium">
              <p style={{ margin: 0 }}>{t('foods.optionalHint')}</p>
            </IonText>
            {nutrientFields(OTHER_NUTRIENTS)}
          </FormSection>
          <FormSection title={t('foods.micronutrients')}>
            {nutrientFields(MICRONUTRIENTS)}
          </FormSection>
          <TranslationsSection
            control={control}
            fields={[{ key: 'name', label: t('catalog.name') }]}
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

export default FoodFormPage;
