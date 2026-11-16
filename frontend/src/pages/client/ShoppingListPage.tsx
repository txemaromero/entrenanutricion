import {
  IonButton,
  IonCheckbox,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  IonListHeader,
  IonSegment,
  IonSegmentButton,
  useIonToast,
} from '@ionic/react';
import { shareSocialOutline } from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { nutritionApi } from '../../api/client-features';
import type { FoodCategory, ShoppingList } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { useResource } from '../../hooks/useResource';
import { offlineStore } from '../../offline/store';
import { formatGrams } from '../../utils/nutrition';

const DAY_OPTIONS = [1, 3, 7, 14] as const;
// Ticks stay on this device, with the other copies of the user (cleared when signing out).
const CHECKED_KEY = 'shopping-checked';

const readChecked = () => new Set(offlineStore.read<number[]>(CHECKED_KEY) ?? []);

/** Foods of the plan's menu for some days, by category, with ticks kept on the device. */
const ShoppingListPage = () => {
  const { t, i18n } = useTranslation();
  const [toast] = useIonToast();
  const [days, setDays] = useState<number>(7);
  const [checked, setChecked] = useState<Set<number>>(readChecked);
  const list = useResource(() => nutritionApi.shoppingList(days), [days]);

  const save = (next: Set<number>) => {
    setChecked(next);
    offlineStore.write(CHECKED_KEY, [...next]);
  };
  const toggle = (foodId: number, value: boolean) => {
    const next = new Set(checked);
    if (value) next.add(foodId);
    else next.delete(foodId);
    save(next);
  };

  const groups = (data: ShoppingList) =>
    data.items.reduce<{ category: FoodCategory; items: ShoppingList['items'] }[]>(
      (result, item) => {
        const last = result[result.length - 1];
        if (last?.category === item.food.category) last.items.push(item);
        else result.push({ category: item.food.category, items: [item] });
        return result;
      },
      [],
    );

  const share = async (data: ShoppingList) => {
    const title = t('shopping.shareTitle', { days: t('shopping.days', { count: data.days }) });
    const text = [
      title,
      ...data.items
        .filter((item) => !checked.has(item.food.id))
        .map((item) => `- ${item.food.name}: ${formatGrams(item.grams, i18n.language)}`),
    ].join('\n');
    try {
      if (navigator.share) {
        await navigator.share({ title, text });
        return;
      }
      await navigator.clipboard.writeText(text);
      void toast({ message: t('shopping.copied'), duration: 2000, color: 'success' });
    } catch {
      /* the user closed the share sheet */
    }
  };

  const pending = list.data?.items.filter((item) => !checked.has(item.food.id)).length ?? 0;

  return (
    <PageLayout
      title={t('shopping.title')}
      backHref={PATHS.nutrition}
      onRefresh={list.reload}
      narrow
      subHeader={
        <IonSegment
          value={String(days)}
          onIonChange={(event) => setDays(Number(event.detail.value))}
          aria-label={t('shopping.daysLabel')}
          data-testid="shopping-days"
        >
          {DAY_OPTIONS.map((value) => (
            <IonSegmentButton
              key={value}
              value={String(value)}
              data-testid={`shopping-days-${value}`}
            >
              <IonLabel>{t('shopping.days', { count: value })}</IonLabel>
            </IonSegmentButton>
          ))}
        </IonSegment>
      }
    >
      <div className="stack">
        <p className="muted" style={{ margin: 0 }}>
          {t('shopping.intro')}
        </p>
        {list.loading && !list.data && <ListSkeleton />}
        {list.error && <ErrorState error={list.error} onRetry={list.reload} />}
        {list.data && !list.data.hasMenu && <EmptyState message={t('shopping.empty')} />}
        {list.data?.hasMenu && (
          <>
            <div className="row row--between row--wrap">
              <strong data-testid="shopping-pending">
                {pending ? t('shopping.itemsLeft', { count: pending }) : t('shopping.allDone')}
              </strong>
              <div className="row">
                {checked.size > 0 && (
                  <IonButton fill="clear" size="small" onClick={() => save(new Set())}>
                    {t('shopping.uncheck')}
                  </IonButton>
                )}
                <IonButton
                  size="small"
                  onClick={() => void share(list.data!)}
                  data-testid="shopping-share"
                >
                  <IonIcon slot="start" icon={shareSocialOutline} aria-hidden="true" />
                  {t('shopping.share')}
                </IonButton>
              </div>
            </div>
            {groups(list.data).map((group) => (
              <IonList key={group.category} lines="full" data-testid={`shopping-${group.category}`}>
                <IonListHeader>
                  <IonLabel>{t(`enums.foodCategory.${group.category}`)}</IonLabel>
                </IonListHeader>
                {group.items.map((item) => (
                  <IonItem key={item.food.id} data-testid={`shopping-item-${item.food.id}`}>
                    <IonCheckbox
                      justify="start"
                      labelPlacement="end"
                      checked={checked.has(item.food.id)}
                      onIonChange={(event) => toggle(item.food.id, event.detail.checked)}
                    >
                      <span className={checked.has(item.food.id) ? 'shopping-done' : undefined}>
                        {item.food.name} · <strong>{formatGrams(item.grams, i18n.language)}</strong>
                      </span>
                    </IonCheckbox>
                  </IonItem>
                ))}
              </IonList>
            ))}
          </>
        )}
      </div>
    </PageLayout>
  );
};

export default ShoppingListPage;
