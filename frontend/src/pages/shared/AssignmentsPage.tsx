import { IonChip, IonItem, IonLabel, IonList } from '@ionic/react';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { assignmentsApi } from '../../api/staff';
import type { PendingUser } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { Avatar } from '../../components/staff/UserProfileBlocks';
import { SearchBox } from '../../components/staff/ManagementCard';
import { useResource } from '../../hooks/useResource';
import { formatDate } from '../../i18n/format';

type Group = 'both' | 'training' | 'nutrition';

const groupOf = (user: PendingUser): Group =>
  user.missing.length === 2 ? 'both' : (user.missing[0] as Group);

const PendingList = ({ users }: { users: PendingUser[] }) => {
  const { t, i18n } = useTranslation();
  return (
    <IonList>
      {users.map((user) => (
        <IonItem
          key={user.id}
          routerLink={`${PATHS.assignments}/${user.id}`}
          detail
          data-testid={`pending-user-${user.id}`}
        >
          <span slot="start">
            <Avatar user={user} size={40} />
          </span>
          <IonLabel>
            <h3>{user.fullName}</h3>
            <p>{user.email}</p>
            <p>
              {t(`enums.goal.${user.goal}`)} ·{' '}
              {t('users.joinedOn', { date: formatDate(user.dateJoined, i18n.language) })}
            </p>
          </IonLabel>
          <div
            slot="end"
            className="row row--wrap"
            style={{ maxWidth: 160, justifyContent: 'flex-end' }}
          >
            {user.missing.map((kind) => (
              <IonChip key={kind} color="tertiary" outline>
                {t(`enums.missing.${kind}`)}
              </IonChip>
            ))}
          </div>
        </IonItem>
      ))}
    </IonList>
  );
};

/** Clients waiting for plans, filtered by role (US-23). Admins see them grouped. */
const AssignmentsPage = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  // The list brings the first 100 (oldest first): the search finds anyone else.
  const [search, setSearch] = useState('');
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const { data, error, loading, reload } = useResource(
    () => assignmentsApi.pending({ search }),
    [search],
  );
  const users = data?.results ?? [];
  const groups: Group[] = ['both', 'training', 'nutrition'];

  return (
    <PageLayout title={t('tabs.assignments')} onRefresh={reload}>
      <SearchBox onSearch={onSearch} testId="assignments-search" />
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && users.length === 0 && search && <EmptyState />}
      {data && users.length === 0 && !search && (
        <EmptyState
          title={t('assignments.allAssigned')}
          message={t('assignments.allAssignedHint')}
        />
      )}
      {users.length > 0 &&
        (user?.role === 'admin' ? (
          groups
            .map((group) => ({ group, items: users.filter((item) => groupOf(item) === group) }))
            .filter(({ items }) => items.length > 0)
            .map(({ group, items }) => (
              <section key={group} data-testid={`pending-group-${group}`}>
                <h2 className="section-title">{t(`enums.missing.${group}`)}</h2>
                <PendingList users={items} />
              </section>
            ))
        ) : (
          <PendingList users={users} />
        ))}
    </PageLayout>
  );
};

export default AssignmentsPage;
