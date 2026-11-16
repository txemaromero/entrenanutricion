import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonCard, IonCardContent, IonIcon, IonText, useIonToast } from '@ionic/react';
import { add, trashOutline } from 'ionicons/icons';
import { useEffect, useRef, useState } from 'react';
import { useFieldArray, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { mealPlansApi } from '../../api/staff';
import type { Meal } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { TextField } from '../../components/form/TextField';
import { FoodPicker, type PickedFood } from '../../components/nutrition/FoodPicker';
import { DeviationChip, NutrientsLine } from '../../components/nutrition/MenuView';
import { FormActions } from '../../components/staff/FormShell';
import { useLeaveForm } from '../../hooks/useLeaveForm';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';
import { translateKey } from '../../utils/errors';
import {
  EMPTY_NUTRIENTS,
  MEAL_KEYS,
  deviationPct,
  per100Of,
  portionOf,
  sumNutrients,
} from '../../utils/nutrition';
import { toNumber } from '../../utils/numbers';
import { menuSchema, type MenuForm } from '../../validation/nutrition';

/** Sample day menu of a nutrition plan: foods and grams per meal, totals against the plan. */
const MenuEditorPage = () => {
  const { t, i18n } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const leave = useLeaveForm(`${PATHS.mealPlans}/${id}`);
  const [toast] = useIonToast();
  const plan = useResource(() => mealPlansApi.get(id), [id]);
  const menu = useResource(() => mealPlansApi.menu(id), [id]);
  const [foods, setFoods] = useState<Record<number, PickedFood>>({});
  const [pickerMeal, setPickerMeal] = useState<Meal | null>(null);
  const [saveError, setSaveError] = useState<unknown>();
  const { control, handleSubmit, reset, formState } = useForm<MenuForm>({
    resolver: zodResolver(menuSchema),
    defaultValues: { items: [] },
  });
  const rows = useFieldArray({ control, name: 'items' });
  const values = useWatch({ control, name: 'items' });

  // Fill the form once: reloads on entering the view must not undo the edits.
  const filled = useRef(false);
  useEffect(() => {
    if (!menu.data || filled.current) return;
    filled.current = true;
    const known: Record<number, PickedFood> = {};
    const items: MenuForm['items'] = [];
    menu.data.meals.forEach((meal) =>
      meal.items.forEach((item) => {
        known[item.food.id] = {
          id: item.food.id,
          name: item.food.name,
          ...per100Of(item, item.grams),
        };
        items.push({ meal: meal.meal, foodId: item.food.id, grams: item.grams });
      }),
    );
    setFoods(known);
    reset({ items });
  }, [menu.data, reset]);

  const n = (value: number) => formatNumber(value, i18n.language, { maximumFractionDigits: 0 });
  const rowPortion = (index: number) => {
    const row = values?.[index];
    const food = row ? foods[row.foodId] : undefined;
    return food && row?.grams ? portionOf(food, row.grams) : EMPTY_NUTRIENTS;
  };
  const indexesOf = (meal: Meal) =>
    rows.fields
      .map((field, index) => ({ field, index }))
      .filter(({ field }) => field.meal === meal);
  const dayTotals = sumNutrients(rows.fields.map((_, index) => rowPortion(index)));

  const onSubmit = handleSubmit(async ({ items }) => {
    setSaveError(undefined);
    try {
      await mealPlansApi.setMenu(id, items);
      void toast({ message: t('menu.saved'), duration: 2000, color: 'success' });
      leave();
    } catch (error) {
      setSaveError(error);
    }
  });

  const loading = (plan.loading && !plan.data) || (menu.loading && !menu.data);
  const error = plan.error ?? menu.error;
  const listError = translateKey(t, formState.errors.items?.root?.message);

  return (
    <PageLayout
      title={plan.data ? t('menu.editTitle', { name: plan.data.name }) : t('menu.title')}
      backHref={`${PATHS.mealPlans}/${id}`}
      narrow
    >
      {loading && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={() => void menu.reload()} />}
      {plan.data && menu.data && (
        <form className="stack" onSubmit={onSubmit} noValidate data-testid="menu-editor">
          <p className="muted" style={{ margin: 0 }}>
            {t('menu.staffIntro')}
          </p>
          <div className="row row--between row--wrap" data-testid="menu-day-totals">
            <NutrientsLine
              value={dayTotals}
              target={{
                calories: plan.data.calories,
                proteinsG: plan.data.proteinsG,
                carbsG: plan.data.carbsG,
                fatsG: plan.data.fatsG,
              }}
            />
            <DeviationChip
              pct={rows.fields.length ? deviationPct(dayTotals.calories, plan.data.calories) : null}
            />
          </div>
          {MEAL_KEYS.map((meal) => {
            const target = plan.data!.meals.find((row) => row.meal === meal);
            const mealRows = indexesOf(meal);
            const totals = sumNutrients(mealRows.map(({ index }) => rowPortion(index)));
            return (
              <IonCard key={meal} className="ion-no-margin" data-testid={`menu-edit-${meal}`}>
                <IonCardContent className="stack">
                  <div className="row row--between row--wrap">
                    <strong>{t(`enums.meal.${meal}`)}</strong>
                    <small className="muted">
                      {t('menu.kcalOfTarget', {
                        kcal: n(totals.calories),
                        target: n(target?.kcal ?? 0),
                      })}
                    </small>
                  </div>
                  {mealRows.map(({ field, index }) => (
                    <div key={field.id} className="menu-row" data-testid={`menu-row-${index}`}>
                      <span>{foods[field.foodId]?.name}</span>
                      <TextField
                        control={control}
                        name={`items.${index}.grams`}
                        label={t('menu.grams')}
                        type="number"
                        inputMode="numeric"
                        parse={toNumber}
                        testId={`menu-grams-${index}`}
                      />
                      <small className="muted">
                        {t('menu.kcal', { kcal: n(rowPortion(index).calories) })}
                      </small>
                      <IonButton
                        fill="clear"
                        color="danger"
                        className="icon-button"
                        onClick={() => rows.remove(index)}
                        aria-label={t('menu.removeFood', { name: foods[field.foodId]?.name })}
                      >
                        <IonIcon slot="icon-only" icon={trashOutline} aria-hidden="true" />
                      </IonButton>
                    </div>
                  ))}
                  <IonButton
                    fill="outline"
                    size="small"
                    style={{ alignSelf: 'flex-start' }}
                    onClick={() => setPickerMeal(meal)}
                    data-testid={`menu-add-${meal}`}
                  >
                    <IonIcon slot="start" icon={add} aria-hidden="true" />
                    {t('menu.addFood')}
                  </IonButton>
                </IonCardContent>
              </IonCard>
            );
          })}
          <small className="muted">{t('menu.toleranceHint')}</small>
          {listError && (
            <IonText color="danger" role="alert">
              <small>{listError}</small>
            </IonText>
          )}
          <FormActions onCancel={() => leave()} saving={formState.isSubmitting} error={saveError} />
        </form>
      )}
      <FoodPicker
        isOpen={pickerMeal !== null}
        title={pickerMeal ? t('menu.pickTitle', { meal: t(`enums.meal.${pickerMeal}`) }) : ''}
        onClose={() => setPickerMeal(null)}
        onDone={async (food, grams) => {
          if (pickerMeal === null || food.id === null) return false;
          setFoods((current) => ({ ...current, [food.id!]: food }));
          rows.append({ meal: pickerMeal, foodId: food.id, grams });
          return true;
        }}
      />
    </PageLayout>
  );
};

export default MenuEditorPage;
