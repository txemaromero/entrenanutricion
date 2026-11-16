import {
  IonButton,
  IonCard,
  IonCardContent,
  IonIcon,
  IonItem,
  IonLabel,
  IonList,
  useIonToast,
} from '@ionic/react';
import {
  add,
  chevronBackOutline,
  chevronForwardOutline,
  copyOutline,
  createOutline,
  trashOutline,
} from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { foodLogApi, nutritionApi } from '../../api/client-features';
import type { DiaryDay, FoodLogEntry, Meal } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ProgressRing } from '../../components/ProgressRing';
import { ErrorState, ListSkeleton } from '../../components/States';
import { DiarySummaryCard } from '../../components/nutrition/DiarySummaryCard';
import { FoodPicker } from '../../components/nutrition/FoodPicker';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber, parseDate, toIsoDate } from '../../i18n/format';
import { errorMessage } from '../../utils/errors';
import { formatGrams, per100Of } from '../../utils/nutrition';

const MACROS = ['proteins', 'carbs', 'fats'] as const;

const shiftDay = (iso: string, delta: number) => {
  const date = parseDate(iso);
  date.setDate(date.getDate() + delta);
  return toIsoDate(date);
};

type Picker = { kind: 'add'; meal: Meal } | { kind: 'edit'; entry: FoodLogEntry };

/** Food diary: what the client ate, day by day, against the targets of the plan. */
const FoodDiaryPage = () => {
  const { t, i18n } = useTranslation();
  const [toast] = useIonToast();
  const today = toIsoDate(new Date());
  const [date, setDate] = useState(today);
  const [picker, setPicker] = useState<Picker | null>(null);
  const day = useResource(() => foodLogApi.day(date), [date]);
  const menu = useResource(nutritionApi.menu);
  const summary = useResource(() => foodLogApi.summary(7));
  const n = (value: number) => formatNumber(value, i18n.language, { maximumFractionDigits: 0 });

  const change = async (action: () => Promise<DiaryDay>, message: string) => {
    try {
      day.setData(await action());
      void summary.reload();
      void toast({ message, duration: 2000, color: 'success' });
      return true;
    } catch (error) {
      void toast({ message: errorMessage(t, error), duration: 3000, color: 'danger' });
      return false;
    }
  };

  const menuMeal = (meal: Meal) => menu.data?.meals.find((row) => row.meal === meal);
  const isEmpty = day.data?.meals.every((meal) => meal.entries.length === 0);
  const target = day.data?.target;
  const totals = day.data?.totals;

  return (
    <PageLayout
      title={t('diary.title')}
      backHref={PATHS.nutrition}
      onRefresh={() => Promise.all([day.reload(), summary.reload()])}
      narrow
    >
      <div className="stack">
        <div className="row row--between" data-testid="diary-date">
          <IonButton
            fill="clear"
            className="icon-button"
            onClick={() => setDate(shiftDay(date, -1))}
            aria-label={t('diary.previousDay')}
            data-testid="diary-previous"
          >
            <IonIcon slot="icon-only" icon={chevronBackOutline} aria-hidden="true" />
          </IonButton>
          <strong data-testid="diary-date-label">
            {date === today
              ? t('diary.today')
              : formatDate(date, i18n.language, { weekday: 'long', day: 'numeric', month: 'long' })}
          </strong>
          <IonButton
            fill="clear"
            className="icon-button"
            disabled={date >= today}
            onClick={() => setDate(shiftDay(date, 1))}
            aria-label={t('diary.nextDay')}
            data-testid="diary-next"
          >
            <IonIcon slot="icon-only" icon={chevronForwardOutline} aria-hidden="true" />
          </IonButton>
        </div>

        {day.loading && !day.data && <ListSkeleton rows={3} />}
        {day.error && <ErrorState error={day.error} onRetry={day.reload} />}
        {day.data && totals && (
          <>
            <IonCard className="ion-no-margin" data-testid="diary-totals">
              <IonCardContent className="stack" style={{ gap: 6 }}>
                <div className="row row--between">
                  <strong>{t('diary.consumed')}</strong>
                  <span>
                    {target
                      ? t('menu.kcalOfTarget', {
                          kcal: n(totals.calories),
                          target: n(target.calories),
                        })
                      : t('menu.kcal', { kcal: n(totals.calories) })}
                  </span>
                </div>
                {target ? (
                  <div className="rings rings--grid" data-testid="diary-rings">
                    <ProgressRing
                      testId="ring-calories"
                      size={76}
                      ratio={totals.calories / target.calories}
                      label={t('diary.ringCalories', {
                        kcal: n(totals.calories),
                        target: n(target.calories),
                      })}
                      caption={t('diary.calories')}
                    >
                      <strong>{n(totals.calories)}</strong>
                      <small>{t('diary.ofTarget', { target: n(target.calories) })}</small>
                    </ProgressRing>
                    {MACROS.map((macro) => (
                      <ProgressRing
                        key={macro}
                        testId={`ring-${macro}`}
                        ratio={totals[`${macro}G`] / target[`${macro}G`]}
                        colorVar={`--en-macro-${macro}`}
                        size={76}
                        label={t('diary.ringMacro', {
                          name: t(`enums.macro.${macro}`),
                          grams: n(totals[`${macro}G`]),
                          target: n(target[`${macro}G`]),
                        })}
                        caption={t(`enums.macro.${macro}`)}
                      >
                        <strong>{n(totals[`${macro}G`])}</strong>
                        <small>{t('diary.ofGrams', { target: n(target[`${macro}G`]) })}</small>
                      </ProgressRing>
                    ))}
                  </div>
                ) : (
                  <small className="muted">{t('diary.noTarget')}</small>
                )}
              </IonCardContent>
            </IonCard>

            {isEmpty && menu.data?.hasMenu && (
              <IonButton
                expand="block"
                fill="outline"
                onClick={() => void change(() => foodLogApi.copyMenu(date), t('diary.menuCopied'))}
                data-testid="diary-copy-day"
              >
                <IonIcon slot="start" icon={copyOutline} aria-hidden="true" />
                {t('diary.copyDay')}
              </IonButton>
            )}

            {day.data.meals.map((meal) => (
              <IonCard
                key={meal.meal}
                className="ion-no-margin"
                data-testid={`diary-meal-${meal.meal}`}
              >
                <IonCardContent className="stack" style={{ gap: 6 }}>
                  <div className="row row--between row--wrap">
                    <strong>{t(`enums.meal.${meal.meal}`)}</strong>
                    <small className="muted">
                      {meal.targetCalories !== null
                        ? t('menu.kcalOfTarget', {
                            kcal: n(meal.totals.calories),
                            target: n(meal.targetCalories),
                          })
                        : t('menu.kcal', { kcal: n(meal.totals.calories) })}
                    </small>
                  </div>
                  {meal.entries.length > 0 && (
                    <IonList lines="full" className="ion-no-padding">
                      {meal.entries.map((entry) => (
                        <IonItem key={entry.id} data-testid={`diary-entry-${entry.id}`}>
                          <IonLabel>
                            <h3>{entry.foodName}</h3>
                            <p>
                              {formatGrams(entry.grams, i18n.language)} ·{' '}
                              {t('menu.kcal', { kcal: n(entry.calories) })}
                            </p>
                          </IonLabel>
                          <IonButton
                            slot="end"
                            fill="clear"
                            className="icon-button"
                            onClick={() => setPicker({ kind: 'edit', entry })}
                            aria-label={t('diary.edit', { name: entry.foodName })}
                            data-testid={`diary-edit-${entry.id}`}
                          >
                            <IonIcon slot="icon-only" icon={createOutline} aria-hidden="true" />
                          </IonButton>
                          <IonButton
                            slot="end"
                            fill="clear"
                            color="danger"
                            className="icon-button"
                            onClick={() =>
                              void change(() => foodLogApi.remove(entry.id), t('diary.removed'))
                            }
                            aria-label={t('diary.remove', { name: entry.foodName })}
                            data-testid={`diary-remove-${entry.id}`}
                          >
                            <IonIcon slot="icon-only" icon={trashOutline} aria-hidden="true" />
                          </IonButton>
                        </IonItem>
                      ))}
                    </IonList>
                  )}
                  <div className="row row--wrap">
                    <IonButton
                      fill="outline"
                      size="small"
                      onClick={() => setPicker({ kind: 'add', meal: meal.meal })}
                      data-testid={`diary-add-${meal.meal}`}
                    >
                      <IonIcon slot="start" icon={add} aria-hidden="true" />
                      {t('diary.add')}
                    </IonButton>
                    {Boolean(menuMeal(meal.meal)?.items.length) && (
                      <IonButton
                        fill="clear"
                        size="small"
                        onClick={() =>
                          void change(
                            () => foodLogApi.copyMenu(date, meal.meal),
                            t('diary.menuCopied'),
                          )
                        }
                        data-testid={`diary-copy-${meal.meal}`}
                      >
                        <IonIcon slot="start" icon={copyOutline} aria-hidden="true" />
                        {t('diary.copyMeal')}
                      </IonButton>
                    )}
                  </div>
                </IonCardContent>
              </IonCard>
            ))}
          </>
        )}

        {summary.data && (
          <DiarySummaryCard summary={summary.data} title={t('diary.summaryTitle')} />
        )}
      </div>

      <FoodPicker
        isOpen={picker !== null}
        title={
          picker?.kind === 'add'
            ? t('diary.addTo', { meal: t(`enums.meal.${picker.meal}`) })
            : t('diary.editTitle')
        }
        food={
          picker?.kind === 'edit'
            ? {
                id: picker.entry.foodId,
                name: picker.entry.foodName,
                ...per100Of(picker.entry, picker.entry.grams),
              }
            : undefined
        }
        defaultGrams={picker?.kind === 'edit' ? picker.entry.grams : 100}
        onClose={() => setPicker(null)}
        onDone={(food, grams) => {
          if (picker?.kind === 'edit') {
            return change(() => foodLogApi.update(picker.entry.id, { grams }), t('diary.saved'));
          }
          if (picker?.kind === 'add' && food.id !== null) {
            return change(
              () => foodLogApi.add({ date, meal: picker.meal, foodId: food.id!, grams }),
              t('diary.saved'),
            );
          }
          return Promise.resolve(false);
        }}
      />
    </PageLayout>
  );
};

export default FoodDiaryPage;
