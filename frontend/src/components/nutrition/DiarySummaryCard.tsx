import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { usersApi } from '../../api/staff';
import type { DiarySummary } from '../../api/types';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber } from '../../i18n/format';
import { BarChart } from '../charts';

/** Calories of the last days against the plan's target (client diary and staff profile). */
export const DiarySummaryCard = ({ summary, title }: { summary: DiarySummary; title: string }) => {
  const { t, i18n } = useTranslation();
  const n = (value: number) => formatNumber(value, i18n.language, { maximumFractionDigits: 0 });
  const target = summary.targetCalories;

  return (
    <IonCard data-testid="diary-summary">
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{title}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        <p className="muted" style={{ margin: 0 }} data-testid="diary-summary-text">
          {summary.daysLogged === 0
            ? t('diary.summaryEmpty')
            : t('diary.summaryText', {
                count: summary.daysLogged,
                days: summary.days.length,
                average: n(summary.averageCalories ?? 0),
              })}
          {target !== null && summary.daysLogged > 0 && (
            <> {t('diary.summaryTarget', { target: n(target) })}</>
          )}
        </p>
        <BarChart
          labels={summary.days.map((day) =>
            formatDate(day.date, i18n.language, { weekday: 'short', day: 'numeric' }),
          )}
          values={summary.days.map((day) => day.calories)}
          label={title}
          seriesLabel={t('diary.consumed')}
          colorVar="--ion-color-primary"
          height={200}
          reference={
            target === null
              ? undefined
              : { value: target, label: t('diary.chartTarget', { kcal: n(target) }) }
          }
          formatValue={(value, index) =>
            summary.days[index].entries ? t('menu.kcal', { kcal: n(value) }) : '—'
          }
          rowTestId="diary-summary-day"
        />
      </IonCardContent>
    </IonCard>
  );
};

/** User profile (staff): the last week of the client's food diary. */
export const ClientDiaryCard = ({ userId }: { userId: number }) => {
  const { t } = useTranslation();
  const { data } = useResource(() => usersApi.foodLogSummary(userId), [userId]);
  return data ? <DiarySummaryCard summary={data} title={t('diary.staffTitle')} /> : null;
};
