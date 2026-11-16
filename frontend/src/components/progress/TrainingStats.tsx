import { IonCard, IonCardContent, IonCardHeader, IonCardTitle } from '@ionic/react';
import { barbellOutline, calendarOutline, fitnessOutline, timeOutline } from 'ionicons/icons';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { progressApi } from '../../api/client-features';
import { useResource } from '../../hooks/useResource';
import { formatDate, formatNumber } from '../../i18n/format';
import { BarChart, LineChart } from '../charts';
import { StatTiles } from '../StatTiles';
import { ErrorState, ListSkeleton } from '../States';

const ChartCard = ({
  title,
  help,
  testId,
  children,
}: {
  title: string;
  help?: string;
  testId: string;
  children: ReactNode;
}) => (
  <IonCard data-testid={testId}>
    <IonCardHeader>
      <IonCardTitle style={{ fontSize: '1.1rem' }}>{title}</IonCardTitle>
      {help && (
        <p className="muted" style={{ margin: '4px 0 0', fontSize: '0.9rem' }}>
          {help}
        </p>
      )}
    </IonCardHeader>
    <IonCardContent>{children}</IonCardContent>
  </IonCard>
);

/** The last 12 weeks in figures and charts: sessions, time, kilos lifted and muscles worked. */
export const TrainingStats = () => {
  const { t, i18n } = useTranslation();
  const stats = useResource(progressApi.stats);
  const language = i18n.language;

  if (stats.error) return <ErrorState error={stats.error} onRetry={stats.reload} />;
  if (!stats.data) return <ListSkeleton rows={2} />;

  const { weeks, muscleGroups } = stats.data;
  const sessions = weeks.reduce((total, week) => total + week.sessions, 0);
  const minutes = weeks.reduce((total, week) => total + week.minutes, 0);
  const volume = weeks.reduce((total, week) => total + week.volumeKg, 0);
  const labels = weeks.map((week) =>
    formatDate(week.start, language, { day: 'numeric', month: 'short' }),
  );
  const kilos = (value: number) =>
    t('progress.stats.kg', {
      value: formatNumber(value, language, { maximumFractionDigits: 0 }),
    });

  return (
    <div className="stack" data-testid="training-stats">
      <IonCard>
        <IonCardHeader>
          <IonCardTitle style={{ fontSize: '1.1rem' }}>
            {t('progress.stats.title', { weeks: weeks.length })}
          </IonCardTitle>
        </IonCardHeader>
        <IonCardContent>
          <StatTiles
            testId="training-totals"
            items={[
              {
                key: 'sessions',
                icon: fitnessOutline,
                label: t('progress.stats.sessions'),
                value: formatNumber(sessions, language),
              },
              {
                key: 'time',
                icon: timeOutline,
                label: t('progress.stats.time'),
                value: t('progress.stats.hours', {
                  value: formatNumber(minutes / 60, language, { maximumFractionDigits: 1 }),
                }),
              },
              {
                key: 'volume',
                icon: barbellOutline,
                label: t('progress.stats.volume'),
                value: kilos(volume),
              },
              {
                key: 'per-week',
                icon: calendarOutline,
                label: t('progress.stats.perWeek'),
                value: formatNumber(weeks.length ? sessions / weeks.length : 0, language, {
                  maximumFractionDigits: 1,
                }),
              },
            ]}
          />
        </IonCardContent>
      </IonCard>

      <ChartCard title={t('progress.stats.sessionsChart')} testId="sessions-per-week">
        <BarChart
          labels={labels}
          values={weeks.map((week) => week.sessions)}
          label={t('progress.stats.sessionsChart')}
          colorVar="--ion-color-primary"
          formatValue={(value, index) =>
            t('progress.stats.sessionsTooltip', { count: value, minutes: weeks[index].minutes })
          }
        />
      </ChartCard>

      <ChartCard
        title={t('progress.stats.volumeChart')}
        help={t('progress.stats.volumeHelp')}
        testId="volume-per-week"
      >
        {volume > 0 ? (
          <LineChart
            labels={labels}
            values={weeks.map((week) => week.volumeKg)}
            label={t('progress.stats.volumeChart')}
            colorVar="--ion-color-primary"
            formatValue={kilos}
          />
        ) : (
          <p className="muted" style={{ margin: 0 }}>
            {t('progress.stats.volumeEmpty')}
          </p>
        )}
      </ChartCard>

      <ChartCard
        title={t('progress.stats.musclesChart')}
        help={t('progress.stats.musclesHelp')}
        testId="muscles-worked"
      >
        {muscleGroups.length > 0 ? (
          <BarChart
            horizontal
            labels={muscleGroups.map((group) =>
              t(`enums.muscleGroup.${group.slug}`, { defaultValue: group.name }),
            )}
            values={muscleGroups.map((group) => group.sets)}
            label={t('progress.stats.musclesChart')}
            colorVar="--ion-color-tertiary"
            formatValue={(value) => t('progress.stats.sets', { count: value })}
          />
        ) : (
          <p className="muted" style={{ margin: 0 }}>
            {t('progress.stats.musclesEmpty')}
          </p>
        )}
      </ChartCard>
    </div>
  );
};
