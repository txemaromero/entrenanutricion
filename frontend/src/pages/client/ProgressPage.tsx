import { IonLabel, IonSegment, IonSegmentButton } from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { progressApi } from '../../api/client-features';
import { MotivationMessage } from '../../components/Motivation';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { BadgesSummaryCard } from '../../components/progress/Badges';
import { HistoryPanel } from '../../components/progress/HistoryPanel';
import { MonthCalendar } from '../../components/progress/MonthCalendar';
import { NextWorkoutCard } from '../../components/progress/NextWorkoutCard';
import { RecordsCard } from '../../components/progress/RecordsCard';
import { TrainingStats } from '../../components/progress/TrainingStats';
import { WeightPanel } from '../../components/progress/WeightPanel';
import { useResource } from '../../hooks/useResource';

type Section = 'control' | 'workout' | 'weight';

const currentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
};

/** Progress with three sticky sub-tabs: Control, Workout and Weight. */
const ProgressPage = () => {
  const { t } = useTranslation();
  const [section, setSection] = useState<Section>('control');
  const [month, setMonth] = useState(currentMonth);
  const dashboard = useResource(() => progressApi.dashboard(month), [month]);
  const weights = useResource(progressApi.weights);

  const reload = () => Promise.all([dashboard.reload(), weights.reload()]);

  return (
    <PageLayout
      title={t('tabs.progress')}
      onRefresh={reload}
      subHeader={
        <IonSegment
          value={section}
          onIonChange={(event) => setSection(event.detail.value as Section)}
          data-testid="progress-segment"
        >
          {(['control', 'workout', 'weight'] as const).map((key) => (
            <IonSegmentButton key={key} value={key} data-testid={`segment-${key}`}>
              <IonLabel>{t(`progress.sections.${key}`)}</IonLabel>
            </IonSegmentButton>
          ))}
        </IonSegment>
      }
    >
      {dashboard.loading && !dashboard.data && <ListSkeleton />}
      {dashboard.error && <ErrorState error={dashboard.error} onRetry={dashboard.reload} />}
      {dashboard.data && (
        <div className="stack">
          <MotivationMessage motivation={dashboard.data.motivation} />
          {section === 'control' && (
            <>
              <MonthCalendar
                month={month}
                completedDays={dashboard.data.completedDays}
                scheduledDays={dashboard.data.scheduledDays}
                onChangeMonth={setMonth}
              />
              <NextWorkoutCard dashboard={dashboard.data} />
              <BadgesSummaryCard />
            </>
          )}
          {section === 'workout' && (
            <>
              <TrainingStats />
              <RecordsCard />
              <HistoryPanel dashboard={dashboard.data} />
            </>
          )}
          {section === 'weight' &&
            (weights.data ? (
              <WeightPanel summary={weights.data} onChange={weights.setData} />
            ) : weights.error ? (
              <ErrorState error={weights.error} onRetry={weights.reload} />
            ) : (
              <ListSkeleton rows={2} />
            ))}
        </div>
      )}
    </PageLayout>
  );
};

export default ProgressPage;
