import { IonButton, IonCard, IonCardContent, IonIcon } from '@ionic/react';
import { bookOutline, cartOutline, nutritionOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { nutritionApi } from '../../api/client-features';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { MacroBreakdown } from '../../components/nutrition/MacroBreakdown';
import { MenuView } from '../../components/nutrition/MenuView';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';

/** Macronutrients (US-08): translated diet type, kcal, macros, donut and meal split. */
const NutritionPage = () => {
  const { t, i18n } = useTranslation();
  const { data: plan, error, loading, reload } = useResource(nutritionApi.myPlan);
  const menu = useResource(nutritionApi.menu);

  return (
    <PageLayout
      title={t('tabs.nutrition')}
      onRefresh={() => Promise.all([reload(), menu.reload()])}
    >
      {loading && !plan && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {plan && (
        <div className="stack">
          <header>
            <h1 style={{ margin: 0 }} data-testid="diet-title">
              {t(`enums.dietLabel.${plan.dietLabel}`)}
            </h1>
            <p className="muted" style={{ margin: '4px 0' }}>
              {t(`enums.mealPlanCategory.${plan.category}`)} · {plan.name}
            </p>
            <p style={{ fontSize: '1.4rem', margin: 0 }} data-testid="diet-kcal">
              <strong>{formatNumber(plan.calories, i18n.language)}</strong>{' '}
              {t('nutrition.kcalPerDay')}
            </p>
          </header>
          <div className="card-grid nutrition-actions">
            <IonButton routerLink={PATHS.foodDiary} data-testid="open-food-diary">
              <IonIcon slot="start" icon={bookOutline} aria-hidden="true" />
              {t('diary.open')}
            </IonButton>
            <IonButton
              fill="outline"
              routerLink={PATHS.shoppingList}
              data-testid="open-shopping-list"
            >
              <IonIcon slot="start" icon={cartOutline} aria-hidden="true" />
              {t('shopping.open')}
            </IonButton>
          </div>
          <MacroBreakdown macros={plan.macros} meals={plan.meals} />
          {menu.data?.hasMenu && (
            <>
              <h2 className="section-title">{t('menu.title')}</h2>
              <p className="muted" style={{ margin: 0 }}>
                {t('menu.intro')}
              </p>
              <MenuView menu={menu.data} />
            </>
          )}
          <IonButton
            expand="block"
            fill="outline"
            routerLink={PATHS.clientFoods}
            data-testid="open-food-library"
          >
            <IonIcon slot="start" icon={nutritionOutline} aria-hidden="true" />
            {t('foods.open')}
          </IonButton>
          {plan.description && (
            <>
              <h2 className="section-title">{t('nutrition.notes')}</h2>
              <IonCard>
                <IonCardContent>{plan.description}</IonCardContent>
              </IonCard>
            </>
          )}
        </div>
      )}
    </PageLayout>
  );
};

export default NutritionPage;
