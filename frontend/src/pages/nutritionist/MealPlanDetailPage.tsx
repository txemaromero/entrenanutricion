import { IonButton, IonCard, IonCardContent, IonChip, IonIcon } from '@ionic/react';
import { createOutline, restaurantOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { mealPlansApi } from '../../api/staff';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { MacroBreakdown } from '../../components/nutrition/MacroBreakdown';
import { MenuView } from '../../components/nutrition/MenuView';
import { useResource } from '../../hooks/useResource';
import { formatNumber } from '../../i18n/format';

/** Read-only nutrition plan: type, kcal, macros donut and meal split. */
const MealPlanDetailPage = () => {
  const { t, i18n } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const { data, error, loading, reload } = useResource(() => mealPlansApi.get(id), [id]);
  const menu = useResource(() => mealPlansApi.menu(id), [id]);

  return (
    <PageLayout
      title={data?.name ?? t('tabs.mealPlans')}
      backHref={data ? `${PATHS.mealPlans}?category=${data.category}` : PATHS.mealPlans}
      actions={
        <IonButton
          routerLink={`${PATHS.mealPlans}/${id}/edit`}
          className="icon-button"
          aria-label={t('common.edit')}
          data-testid="detail-edit"
        >
          <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
        </IonButton>
      }
    >
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack" data-testid="meal-plan-detail">
          <h1 style={{ margin: 0 }}>{data.name}</h1>
          <div className="row row--wrap">
            <IonChip color="primary">{t(`enums.dietLabel.${data.dietLabel}`)}</IonChip>
            <IonChip>{t(`enums.mealPlanCategory.${data.category}`)}</IonChip>
            {!data.isActive && <IonChip color="medium">{t('catalog.inactive')}</IonChip>}
          </div>
          <p style={{ fontSize: '1.3rem', margin: 0 }}>
            <strong>{formatNumber(data.calories, i18n.language)}</strong>{' '}
            {t('nutrition.kcalPerDay')}
          </p>
          <MacroBreakdown macros={data.macros} meals={data.meals} />
          <h2 className="section-title">{t('menu.title')}</h2>
          {menu.data?.hasMenu ? (
            <MenuView menu={menu.data} showDeviation />
          ) : (
            <p className="muted" style={{ margin: 0 }} data-testid="menu-empty">
              {t('menu.empty')}
            </p>
          )}
          <IonButton
            fill="outline"
            routerLink={`${PATHS.mealPlans}/${id}/menu`}
            data-testid="edit-menu"
          >
            <IonIcon slot="start" icon={restaurantOutline} aria-hidden="true" />
            {t('menu.edit')}
          </IonButton>
          {data.description && (
            <IonCard>
              <IonCardContent>{data.description}</IonCardContent>
            </IonCard>
          )}
        </div>
      )}
    </PageLayout>
  );
};

export default MealPlanDetailPage;
