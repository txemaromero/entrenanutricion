import {
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonSelect,
  IonSelectOption,
} from '@ionic/react';
import {
  barbellOutline,
  checkmarkCircleOutline,
  documentTextOutline,
  hourglassOutline,
  peopleOutline,
  shieldCheckmarkOutline,
} from 'ionicons/icons';
import { useState, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { statisticsApi } from '../../api/staff';
import type { Goal, StatisticsSummary } from '../../api/types';
import { BarChart, DonutChart } from '../../components/charts';
import { PageLayout } from '../../components/PageLayout';
import { StatTiles, type StatTrend } from '../../components/StatTiles';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { useResource } from '../../hooks/useResource';
import { formatNumber, monthName } from '../../i18n/format';

/** Goals and their keys once the API layer has turned them into camelCase. */
const GOALS: [Goal, keyof StatisticsSummary['clientsByGoal']][] = [
  ['lose_weight', 'loseWeight'],
  ['gain_muscle', 'gainMuscle'],
  ['maintain', 'maintain'],
];

/** Comparison with the same days of the previous month, as an arrow and words. */
const trend = (
  t: (key: string, options?: Record<string, unknown>) => string,
  current: number,
  previous: number,
): StatTrend => {
  if (current === previous) return { direction: 'flat', text: t('statistics.trend.same') };
  const direction = current > previous ? 'up' : 'down';
  return {
    direction,
    text: t(`statistics.trend.${direction === 'up' ? 'more' : 'less'}`, {
      count: Math.abs(current - previous),
    }),
  };
};

const ChartCard = ({ title, children }: { title: string; children: ReactNode }) => (
  <IonCard>
    <IonCardHeader>
      <IonCardTitle style={{ fontSize: '1.05rem' }}>{title}</IonCardTitle>
    </IonCardHeader>
    <IonCardContent>{children}</IonCardContent>
  </IonCard>
);

const Kpis = ({ summary }: { summary: StatisticsSummary }) => {
  const { t, i18n } = useTranslation();
  const n = (value: number) => formatNumber(value, i18n.language);
  const team =
    summary.usersByRole.trainer + summary.usersByRole.nutritionist + summary.usersByRole.admin;

  return (
    <StatTiles
      items={[
        {
          key: 'clients',
          testId: 'kpi-clients',
          icon: peopleOutline,
          label: t('statistics.clients'),
          value: n(summary.usersByRole.client),
          trend: {
            ...trend(t, summary.newClientsThisMonth, summary.newClientsPreviousPeriod),
            text: t('statistics.newThisMonth', { count: summary.newClientsThisMonth }),
          },
        },
        {
          key: 'active',
          testId: 'kpi-active',
          icon: checkmarkCircleOutline,
          label: t('statistics.activeClients'),
          value: n(summary.activeClients),
        },
        {
          key: 'pending',
          testId: 'kpi-pending',
          icon: hourglassOutline,
          label: t('statistics.pendingAssignment'),
          value: n(summary.pendingAssignment),
        },
        {
          key: 'onboarding',
          testId: 'kpi-onboarding',
          icon: documentTextOutline,
          label: t('statistics.pendingOnboarding'),
          value: n(summary.pendingOnboarding),
        },
        {
          key: 'sessions',
          testId: 'kpi-sessions',
          icon: barbellOutline,
          label: t('statistics.sessionsThisMonth'),
          value: n(summary.sessionsThisMonth),
          trend: trend(t, summary.sessionsThisMonth, summary.sessionsPreviousPeriod),
        },
        {
          key: 'team',
          testId: 'kpi-team',
          icon: shieldCheckmarkOutline,
          label: t('statistics.team'),
          hint: [
            t('statistics.teamTrainers', { count: summary.usersByRole.trainer }),
            t('statistics.teamNutritionists', { count: summary.usersByRole.nutritionist }),
            t('statistics.teamAdmins', { count: summary.usersByRole.admin }),
          ].join(' · '),
          value: n(team),
        },
      ]}
    />
  );
};

/** Admin statistics (US-24): KPIs with their trend, clients by status and goal, and per year
 * the sessions, the new clients, the most used exercises and the plans with most clients. */
const StatisticsPage = () => {
  const { t, i18n } = useTranslation();
  const [year, setYear] = useState(new Date().getFullYear());
  const years = useResource(statisticsApi.years);
  const summary = useResource(statisticsApi.summary);
  const plans = useResource(statisticsApi.planPopularity);
  const charts = useResource(
    () =>
      Promise.all([
        statisticsApi.popularity(year),
        statisticsApi.growth(year),
        statisticsApi.sessions(year),
      ]),
    [year],
  );
  const reload = () =>
    Promise.all([years.reload(), summary.reload(), plans.reload(), charts.reload()]);
  const [popularity, growth, sessions] = charts.data ?? [[], [], []];
  const months = (rows: { month: number }[]) =>
    rows.map((row) => monthName(row.month, i18n.language));
  const clients = (value: number) => t('statistics.clientsCount', { count: value });

  return (
    <PageLayout title={t('tabs.statistics')} onRefresh={reload}>
      <div className="stack">
        {summary.error && <ErrorState error={summary.error} onRetry={summary.reload} />}
        {summary.data && (
          <>
            <Kpis summary={summary.data} />
            <div className="card-grid">
              <ChartCard title={t('statistics.byStatus')}>
                <DonutChart
                  testId="status-chart"
                  label={t('statistics.byStatus')}
                  labels={[
                    t('enums.userStatus.active'),
                    t('enums.userStatus.pending_assignment'),
                    t('enums.userStatus.pending_onboarding'),
                  ]}
                  values={[
                    summary.data.activeClients,
                    summary.data.pendingAssignment,
                    summary.data.pendingOnboarding,
                  ]}
                  colorVars={['--ion-color-success', '--ion-color-warning', '--ion-color-medium']}
                  centre={
                    <>
                      <strong>
                        {formatNumber(summary.data.usersByRole.client, i18n.language)}
                      </strong>
                      <small>{t('statistics.clientsShort')}</small>
                    </>
                  }
                />
              </ChartCard>
              <ChartCard title={t('statistics.byGoal')}>
                <DonutChart
                  testId="goal-chart"
                  label={t('statistics.byGoal')}
                  labels={GOALS.map(([goal]) => t(`enums.goal.${goal}`))}
                  values={GOALS.map(([, key]) => summary.data!.clientsByGoal[key])}
                  colorVars={GOALS.map((_, index) => `--en-series-${index + 1}`)}
                />
              </ChartCard>
            </div>
          </>
        )}

        <IonSelect
          label={t('statistics.year')}
          labelPlacement="floating"
          fill="outline"
          interface="popover"
          value={year}
          onIonChange={(event) => setYear(event.detail.value)}
          style={{ maxWidth: 220 }}
          data-testid="year-select"
        >
          {(years.data ?? [year]).map((value) => (
            <IonSelectOption key={value} value={value}>
              {value}
            </IonSelectOption>
          ))}
        </IonSelect>

        {charts.loading && !charts.data && <ListSkeleton rows={2} />}
        {charts.error && <ErrorState error={charts.error} onRetry={charts.reload} />}
        {charts.data && (
          <>
            <div className="card-grid">
              <ChartCard title={t('statistics.sessions', { year })}>
                <BarChart
                  testId="sessions-chart"
                  label={t('statistics.sessions', { year })}
                  colorVar="--ion-color-primary"
                  labels={months(sessions)}
                  values={sessions.map((row) => row.count)}
                />
              </ChartCard>
              <ChartCard title={t('statistics.growth', { year })}>
                <BarChart
                  testId="growth-chart"
                  label={t('statistics.growth', { year })}
                  colorVar="--ion-color-primary"
                  labels={months(growth)}
                  values={growth.map((row) => row.count)}
                  formatValue={clients}
                />
              </ChartCard>
            </div>
            <ChartCard title={t('statistics.popularity', { year })}>
              {popularity.length === 0 ? (
                <EmptyState message={t('statistics.noData')} />
              ) : (
                <BarChart
                  horizontal
                  testId="popularity-chart"
                  label={t('statistics.popularity', { year })}
                  colorVar="--ion-color-tertiary"
                  labels={popularity.map((row) => row.name)}
                  values={popularity.map((row) => row.count)}
                />
              )}
            </ChartCard>
          </>
        )}

        {plans.data && (
          <div className="card-grid">
            {(['training', 'nutrition'] as const).map((kind) => (
              <ChartCard key={kind} title={t(`statistics.plans.${kind}`)}>
                {plans.data![kind].length === 0 ? (
                  <EmptyState message={t('statistics.plans.empty')} />
                ) : (
                  <BarChart
                    horizontal
                    testId={`plans-${kind}`}
                    label={t(`statistics.plans.${kind}`)}
                    colorVar={kind === 'training' ? '--ion-color-primary' : '--ion-color-tertiary'}
                    labels={plans.data![kind].map((row) => row.name)}
                    values={plans.data![kind].map((row) => row.count)}
                    formatValue={clients}
                  />
                )}
              </ChartCard>
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
};

export default StatisticsPage;
