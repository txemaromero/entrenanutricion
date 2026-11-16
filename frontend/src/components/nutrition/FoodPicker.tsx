import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonButtons,
  IonContent,
  IonHeader,
  IonItem,
  IonLabel,
  IonList,
  IonModal,
  IonNote,
  IonTitle,
  IonToolbar,
} from '@ionic/react';
import { useCallback, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { foodsApi } from '../../api/foods';
import type { Nutrients } from '../../api/types';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';
import { portionOf } from '../../utils/nutrition';
import { toNumber } from '../../utils/numbers';
import { portionSchema, type PortionForm } from '../../validation/nutrition';
import { TextField } from '../form/TextField';
import { SearchBox } from '../staff/ManagementCard';
import { EmptyState, ErrorState, ListSkeleton } from '../States';

/** A food with its values per 100 g (from the library, or worked out from a logged portion). */
export interface PickedFood extends Nutrients {
  id: number | null;
  name: string;
}

/**
 * Modal to choose a food of the library and its grams, or (with `food`) only change the grams.
 * Shows the calories and macros of the portion while typing.
 */
export const FoodPicker = ({
  isOpen,
  title,
  food: fixedFood,
  defaultGrams = 100,
  onClose,
  onDone,
}: {
  isOpen: boolean;
  title: string;
  /** Skip the search: only the grams of this food. */
  food?: PickedFood;
  defaultGrams?: number;
  onClose: () => void;
  /** Resolves to true when it was saved (the modal closes). */
  onDone: (food: PickedFood, grams: number) => Promise<boolean>;
}) => {
  const { t, i18n } = useTranslation();
  const [search, setSearch] = useState('');
  const [picked, setPicked] = useState<PickedFood | null>(null);
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const foods = useResource(
    () => (isOpen && !fixedFood ? foodsApi.list({ search }) : Promise.resolve(null)),
    [isOpen, Boolean(fixedFood), search],
  );
  const { control, handleSubmit, reset, formState } = useForm<PortionForm>({
    resolver: zodResolver(portionSchema),
    defaultValues: { grams: defaultGrams },
  });
  const grams = useWatch({ control, name: 'grams' });
  const food = fixedFood ?? picked;
  const n = (value: number) => formatNumber(value, i18n.language);

  // Every time it opens: no food chosen, no search and the default grams.
  const onOpen = () => {
    setPicked(null);
    setSearch('');
    reset({ grams: defaultGrams });
  };

  const onSubmit = handleSubmit(async (values) => {
    if (food && (await onDone(food, values.grams))) onClose();
  });
  const portion = food && grams ? portionOf(food, grams) : null;

  return (
    <IonModal
      isOpen={isOpen}
      onWillPresent={onOpen}
      onDidDismiss={onClose}
      data-testid="food-picker"
    >
      <IonHeader>
        <IonToolbar>
          <IonTitle>{title}</IonTitle>
          <IonButtons slot="end">
            <IonButton onClick={onClose} data-testid="food-picker-close">
              {t('common.close')}
            </IonButton>
          </IonButtons>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        {!food && (
          <div className="stack">
            <SearchBox onSearch={onSearch} testId="food-picker-search" />
            {foods.loading && !foods.data && <ListSkeleton rows={3} />}
            {foods.error && <ErrorState error={foods.error} onRetry={foods.reload} />}
            {foods.data && foods.data.results.length === 0 && <EmptyState />}
            {foods.data && foods.data.results.length > 0 && (
              <IonList lines="full">
                {foods.data.results.map((item) => (
                  <IonItem
                    key={item.id}
                    button
                    detail
                    onClick={() => setPicked(item)}
                    data-testid={`pick-food-${item.id}`}
                  >
                    <IonLabel>
                      <h3>{item.name}</h3>
                      <p>{t(`enums.foodCategory.${item.category}`)}</p>
                    </IonLabel>
                    <IonNote slot="end">{t('menu.per100', { kcal: n(item.calories) })}</IonNote>
                  </IonItem>
                ))}
              </IonList>
            )}
          </div>
        )}
        {food && (
          <form className="stack" onSubmit={onSubmit} noValidate data-testid="portion-form">
            <h2 style={{ margin: 0 }} data-testid="picked-food">
              {food.name}
            </h2>
            <p className="muted" style={{ margin: 0 }}>
              {t('menu.per100', { kcal: n(food.calories) })}
            </p>
            <TextField
              control={control}
              name="grams"
              label={t('menu.grams')}
              type="number"
              inputMode="numeric"
              parse={toNumber}
              required
              testId="portion-grams"
            />
            {portion && (
              <p style={{ margin: 0 }} data-testid="portion-preview">
                <strong>
                  {n(portion.calories)} {t('common.kcal')}
                </strong>{' '}
                ·{' '}
                {t('nutrition.macroGrams', {
                  proteins: n(portion.proteinsG),
                  carbs: n(portion.carbsG),
                  fats: n(portion.fatsG),
                })}
              </p>
            )}
            <div className="row row--wrap">
              {!fixedFood && (
                <IonButton fill="clear" onClick={() => setPicked(null)}>
                  {t('menu.otherFood')}
                </IonButton>
              )}
              <IonButton type="submit" disabled={formState.isSubmitting} data-testid="portion-save">
                {fixedFood ? t('common.save') : t('menu.add')}
              </IonButton>
            </div>
          </form>
        )}
      </IonContent>
    </IonModal>
  );
};
