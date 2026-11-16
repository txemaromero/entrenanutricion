import { useTranslation } from 'react-i18next';

import { progressApi } from '../../api/client-features';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { BadgeGrid } from '../../components/progress/Badges';
import { useResource } from '../../hooks/useResource';

/** Gamification (phase 9): every badge with its progress. */
const BadgesPage = () => {
  const { t } = useTranslation();
  const { data, error, loading, reload } = useResource(progressApi.badges);

  return (
    <PageLayout title={t('badges.title')} backHref={PATHS.progress} onRefresh={reload}>
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && (
        <div className="stack">
          <p className="muted" style={{ margin: 0 }}>
            {t('badges.intro')}
          </p>
          <p style={{ margin: 0 }} data-testid="badges-count">
            <strong>{t('badges.summary', { earned: data.earnedCount, total: data.total })}</strong>
          </p>
          <BadgeGrid badges={data.badges} />
        </div>
      )}
    </PageLayout>
  );
};

export default BadgesPage;
