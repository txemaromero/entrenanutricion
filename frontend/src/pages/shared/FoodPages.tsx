import {
  IonButton,
  IonChip,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonNote,
  IonSelect,
  IonSelectOption,
} from '@ionic/react';
import { createOutline } from 'ionicons/icons';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { foodsApi } from '../../api/foods';
import type { Food, FoodCategory } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { MacroBreakdown } from '../../components/nutrition/MacroBreakdown';
import { AddFab, ManagementCard, SearchBox } from '../../components/staff/ManagementCard';
import { useDeleteAction } from '../../hooks/useDeleteAction';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';
import {
  FOOD_CATEGORIES,
  MICRONUTRIENTS,
  OTHER_NUTRIENTS,
  knownNutrients,
  type NutrientKey,
} from '../../utils/foods';

/** Nutritionists and admins manage the library from Nutrition plans; clients browse it. */
const pathsFor = (editable: boolean) =>
  editable
    ? { base: PATHS.foods, back: PATHS.mealPlans }
    : { base: PATHS.clientFoods, back: PATHS.nutrition };

const FoodsList = ({ editable }: { editable: boolean }) => {
  const { t, i18n } = useTranslation();
  const remove = useDeleteAction();
  const { base, back } = pathsFor(editable);
  const [category, setCategory] = useState<FoodCategory | ''>('');
  const [search, setSearch] = useState('');
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const { data, error, loading, reload } = useResource(
    () => foodsApi.list({ search, category }),
    [search, category],
  );
  const n = (value: number) => formatNumber(value, i18n.language);

  return (
    <PageLayout
      title={t('foods.title')}
      backHref={back}
      onRefresh={reload}
      overlay={editable ? <AddFab href={`${base}/new`} label={t('foods.new')} /> : undefined}
    >
      <p className="muted" style={{ marginTop: 0 }}>
        {t('foods.intro')}
      </p>
      <SearchBox onSearch={onSearch} testId="food-search" />
      <IonSelect
        label={t('foods.category')}
        labelPlacement="floating"
        fill="outline"
        interface="popover"
        value={category}
        onIonChange={(event) => setCategory(event.detail.value as FoodCategory | '')}
        data-testid="food-category"
      >
        <IonSelectOption value="">{t('foods.allCategories')}</IonSelectOption>
        {FOOD_CATEGORIES.map((key) => (
          <IonSelectOption key={key} value={key}>
            {t(`enums.foodCategory.${key}`)}
          </IonSelectOption>
        ))}
      </IonSelect>
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && data.results.length === 0 && <EmptyState />}
      {data && data.results.length > 0 && (
        <div className="card-grid" style={{ marginTop: 12 }}>
          {data.results.map((food) => (
            <ManagementCard
              key={food.id}
              testId={`food-card-${food.id}`}
              title={food.name}
              subtitle={t(`enums.foodCategory.${food.category}`)}
              viewHref={`${base}/${food.id}`}
              editHref={editable ? `${base}/${food.id}/edit` : undefined}
              onDelete={
                editable
                  ? () =>
                      void remove({
                        name: food.name,
                        remove: () => foodsApi.remove(food.id),
                        onDone: reload,
                      })
                  : undefined
              }
            >
              <p style={{ margin: 0 }}>
                <strong>{t('foods.kcalPer100g', { kcal: n(food.calories) })}</strong>
              </p>
              <p className="muted" style={{ margin: 0 }}>
                {t('foods.macroLine', {
                  proteins: n(food.proteinsG),
                  carbs: n(food.carbsG),
                  fats: n(food.fatsG),
                })}
              </p>
            </ManagementCard>
          ))}
        </div>
      )}
      <p className="muted">
        <small>{t('foods.disclaimer')}</small>
      </p>
    </PageLayout>
  );
};

const NutrientList = ({
  food,
  nutrients,
  testId,
}: {
  food: Food;
  nutrients: [NutrientKey, string][];
  testId: string;
}) => {
  const { t, i18n } = useTranslation();
  return (
    <IonList inset data-testid={testId}>
      {nutrients.map(([key, unit]) => (
        <IonItem key={key}>
          <IonLabel>{t(`foods.nutrients.${key}`)}</IonLabel>
          <IonNote slot="end" color="dark">
            {formatNumber(food[key] ?? 0, i18n.language)} {unit}
          </IonNote>
        </IonItem>
      ))}
    </IonList>
  );
};

const FoodDetail = ({ editable }: { editable: boolean }) => {
  const { t, i18n } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { base } = pathsFor(editable);
  const { data, error, loading, reload } = useResource(() => foodsApi.get(id), [id]);
  const others = data ? knownNutrients(data, OTHER_NUTRIENTS) : [];
  const micros = data ? knownNutrients(data, MICRONUTRIENTS) : [];

  return (
    <PageLayout
      title={data?.name ?? t('foods.title')}
      backHref={base}
      actions={
        editable ? (
          <IonButton
            routerLink={`${base}/${id}/edit`}
            className="icon-button"
            aria-label={t('common.edit')}
            data-testid="detail-edit"
          >
            <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
          </IonButton>
        ) : undefined
      }
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="food-detail">
          <h1 style={{ margin: 0 }}>{data.name}</h1>
          <div className="row row--wrap">
            <IonChip>{t(`enums.foodCategory.${data.category}`)}</IonChip>
            <IonChip color="primary">{t('foods.per100g')}</IonChip>
          </div>
          <p style={{ fontSize: '1.3rem', margin: 0 }} data-testid="food-kcal">
            <strong>
              {t('foods.kcalPer100g', { kcal: formatNumber(data.calories, i18n.language) })}
            </strong>
          </p>
          <MacroBreakdown macros={data.macros} />
          {others.length > 0 && (
            <>
              <h2 className="section-title">{t('foods.otherNutrients')}</h2>
              <NutrientList food={data} nutrients={others} testId="food-other-nutrients" />
            </>
          )}
          <h2 className="section-title">{t('foods.micronutrients')}</h2>
          {micros.length > 0 ? (
            <NutrientList food={data} nutrients={micros} testId="food-micronutrients" />
          ) : (
            <p className="muted">{t('foods.noMicronutrients')}</p>
          )}
          <p className="muted">
            <small>{t('foods.disclaimer')}</small>
          </p>
        </div>
      )}
    </PageLayout>
  );
};

export const StaffFoodsPage = () => <FoodsList editable />;
export const ClientFoodsPage = () => <FoodsList editable={false} />;
export const StaffFoodDetailPage = () => <FoodDetail editable />;
export const ClientFoodDetailPage = () => <FoodDetail editable={false} />;
