import { IonButton, IonIcon, IonLabel, IonSegment, IonSegmentButton } from '@ionic/react';
import { nutritionOutline } from 'ionicons/icons';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useHistory, useLocation } from 'react-router-dom';

import { mealPlansApi } from '../../api/staff';
import type { MealPlanCategory } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { AddFab, ManagementCard, SearchBox } from '../../components/staff/ManagementCard';
import { useDeleteAction } from '../../hooks/useDeleteAction';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';
import { queryParam } from '../../utils/lists';
import { CATEGORIES } from '../../validation/staff';

/** Nutrition plans by category (Weight loss | Muscle gain | Maintenance). */
const MealPlansPage = () => {
  const { t, i18n } = useTranslation();
  const history = useHistory();
  const location = useLocation();
  const remove = useDeleteAction();
  const initial = queryParam(location.search, 'category') as MealPlanCategory | null;
  const [category, setCategory] = useState<MealPlanCategory>(
    initial && CATEGORIES.includes(initial) ? initial : 'weight_loss',
  );
  const [search, setSearch] = useState('');
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const { data, error, loading, reload } = useResource(
    () => mealPlansApi.list({ category, search }),
    [category, search],
  );

  const changeCategory = (next: MealPlanCategory) => {
    setCategory(next);
    history.replace(`${PATHS.mealPlans}?category=${next}`);
  };

  return (
    <PageLayout
      title={t('tabs.mealPlans')}
      onRefresh={reload}
      subHeader={
        <IonSegment
          value={category}
          onIonChange={(event) => changeCategory(event.detail.value as MealPlanCategory)}
        >
          {CATEGORIES.map((key) => (
            <IonSegmentButton key={key} value={key} data-testid={`category-${key}`}>
              <IonLabel>{t(`enums.mealPlanCategory.${key}`)}</IonLabel>
            </IonSegmentButton>
          ))}
        </IonSegment>
      }
      overlay={
        <AddFab href={`${PATHS.mealPlans}/new?category=${category}`} label={t('mealPlans.new')} />
      }
    >
      <IonButton
        fill="outline"
        size="small"
        routerLink={PATHS.foods}
        data-testid="open-food-library"
      >
        <IonIcon slot="start" icon={nutritionOutline} aria-hidden="true" />
        {t('foods.open')}
      </IonButton>
      <SearchBox onSearch={onSearch} />
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && data.results.length === 0 && <EmptyState />}
      {data && data.results.length > 0 && (
        <div className="card-grid">
          {data.results.map((plan) => (
            <ManagementCard
              key={plan.id}
              testId={`meal-plan-card-${plan.id}`}
              title={plan.name}
              subtitle={t(`enums.dietLabel.${plan.dietLabel}`)}
              viewHref={`${PATHS.mealPlans}/${plan.id}`}
              editHref={`${PATHS.mealPlans}/${plan.id}/edit`}
              onDelete={() =>
                void remove({
                  name: plan.name,
                  remove: () => mealPlansApi.remove(plan.id),
                  onDone: reload,
                })
              }
            >
              <p style={{ margin: 0 }}>
                <strong>{formatNumber(plan.calories, i18n.language)}</strong> {t('common.kcal')} ·{' '}
                {t('nutrition.macroGrams', {
                  proteins: formatNumber(plan.proteinsG, i18n.language),
                  carbs: formatNumber(plan.carbsG, i18n.language),
                  fats: formatNumber(plan.fatsG, i18n.language),
                })}
              </p>
            </ManagementCard>
          ))}
        </div>
      )}
    </PageLayout>
  );
};

export default MealPlansPage;
