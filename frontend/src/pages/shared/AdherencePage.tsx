import { IonLabel, IonSegment, IonSegmentButton } from '@ionic/react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { adherenceApi } from '../../api/staff';
import type { AdherenceStatus } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { AdherenceCard } from '../../components/staff/Adherence';
import { AdherenceOverview } from '../../components/staff/AdherenceOverview';
import { SearchBox } from '../../components/staff/ManagementCard';
import { useResource } from '../../hooks/useResource';

const STATUSES: AdherenceStatus[] = ['inactive', 'at_risk', 'on_track'];

/** Staff: clients with a plan, worst adherence first, filterable by status. */
const AdherencePage = () => {
  const { t } = useTranslation();
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<AdherenceStatus | ''>('');
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const { data, error, loading, reload } = useResource(
    () => adherenceApi.list({ search, status }),
    [search, status],
  );
  const count = (value: AdherenceStatus) =>
    data?.counts.find((entry) => entry.status === value)?.count;

  return (
    <PageLayout title={t('adherence.title')} backHref={PATHS.users} onRefresh={reload}>
      <div className="stack">
        <p className="muted" style={{ margin: 0 }}>
          {t('adherence.intro')}
        </p>
        {data && <AdherenceOverview data={data} />}
        <SearchBox onSearch={onSearch} />
        <IonSegment
          scrollable
          value={status || 'all'}
          onIonChange={(event) =>
            setStatus(event.detail.value === 'all' ? '' : (event.detail.value as AdherenceStatus))
          }
          data-testid="adherence-filter"
        >
          <IonSegmentButton value="all" data-testid="adherence-filter-all">
            <IonLabel>{t('adherence.all')}</IonLabel>
          </IonSegmentButton>
          {STATUSES.map((value) => (
            <IonSegmentButton key={value} value={value} data-testid={`adherence-filter-${value}`}>
              <IonLabel>
                {t(`enums.adherenceStatus.${value}`)}
                {count(value) !== undefined && ` (${count(value)})`}
              </IonLabel>
            </IonSegmentButton>
          ))}
        </IonSegment>
        {loading && !data && <ListSkeleton />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && data.results.length === 0 && <EmptyState message={t('adherence.empty')} />}
        {data && data.results.length > 0 && (
          <div className="card-grid" data-testid="adherence-list">
            {data.results.map((row) => (
              <AdherenceCard key={row.user.id} row={row} />
            ))}
          </div>
        )}
      </div>
    </PageLayout>
  );
};

export default AdherencePage;
