import {
  IonButton,
  IonChip,
  IonIcon,
  IonLabel,
  IonSelect,
  IonSelectOption,
  useIonRouter,
} from '@ionic/react';
import {
  checkmarkCircleOutline,
  closeCircleOutline,
  documentTextOutline,
  hourglassOutline,
  pulseOutline,
} from 'ionicons/icons';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { usersApi } from '../../api/staff';
import type { Role, UserStatus } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { NotesInboxCard } from '../../components/notes/StaffNotes';
import { PageLayout } from '../../components/PageLayout';
import { EmptyState, ErrorState, ListSkeleton } from '../../components/States';
import { AddFab, ManagementCard, SearchBox } from '../../components/staff/ManagementCard';
import { Avatar, PlanChips } from '../../components/staff/UserProfileBlocks';
import { useDeleteAction } from '../../hooks/useDeleteAction';
import { useResource } from '../../hooks/useResource';
import { ROLES } from '../../validation/staff';

/** Users (US-20): alphabetical, searchable, role filter. Edit/delete/create only for admins. */
/** Each status of a client with an icon and a colour (never the colour alone). */
const STATUS_STYLE: Record<UserStatus, { icon: string; color: string }> = {
  active: { icon: checkmarkCircleOutline, color: 'success' },
  pending_assignment: { icon: hourglassOutline, color: 'warning' },
  pending_onboarding: { icon: documentTextOutline, color: 'medium' },
  inactive: { icon: closeCircleOutline, color: 'danger' },
};

const UsersPage = () => {
  const { t } = useTranslation();
  const router = useIonRouter();
  const { user: me } = useAuth();
  const isAdmin = me?.role === 'admin';
  const remove = useDeleteAction();
  const [search, setSearch] = useState('');
  const [role, setRole] = useState<Role | ''>('');
  const onSearch = useCallback((value: string) => setSearch(value), []);
  const { data, error, loading, reload } = useResource(
    () => usersApi.list({ search, role }),
    [search, role],
  );

  return (
    <PageLayout
      title={t('tabs.users')}
      onRefresh={reload}
      overlay={isAdmin ? <AddFab href={`${PATHS.users}/new`} label={t('users.new')} /> : undefined}
    >
      <IonButton
        fill="outline"
        size="small"
        routerLink={PATHS.adherence}
        data-testid="open-adherence"
      >
        <IonIcon slot="start" icon={pulseOutline} aria-hidden="true" />
        {t('adherence.open')}
      </IonButton>
      <NotesInboxCard />
      <div className="row row--wrap">
        <div style={{ flex: '2 1 240px' }}>
          <SearchBox onSearch={onSearch} />
        </div>
        {/* The API only gives trainers and nutritionists the clients: nothing to filter. */}
        {isAdmin && (
          <IonSelect
            style={{ flex: '1 1 160px' }}
            label={t('users.roleFilter')}
            labelPlacement="floating"
            fill="outline"
            interface="popover"
            value={role}
            onIonChange={(event) => setRole(event.detail.value)}
            data-testid="role-filter"
          >
            <IonSelectOption value="">{t('users.allRoles')}</IonSelectOption>
            {ROLES.map((value) => (
              <IonSelectOption key={value} value={value}>
                {t(`enums.role.${value}`)}
              </IonSelectOption>
            ))}
          </IonSelect>
        )}
      </div>
      {loading && !data && <ListSkeleton />}
      {error && <ErrorState error={error} onRetry={reload} />}
      {data && data.results.length === 0 && <EmptyState />}
      {data && data.results.length > 0 && (
        <div className="card-grid">
          {data.results.map((user) => (
            <ManagementCard
              key={user.id}
              testId={`user-card-${user.id}`}
              title={user.fullName}
              subtitle={user.email}
              viewHref={`${PATHS.users}/${user.id}`}
              onAssign={
                user.role === 'client' && user.status !== 'pending_onboarding'
                  ? () => router.push(`${PATHS.assignments}/${user.id}`)
                  : undefined
              }
              editHref={isAdmin ? `${PATHS.users}/${user.id}/edit` : undefined}
              onDelete={
                isAdmin && user.id !== me?.id
                  ? () =>
                      void remove({
                        name: user.fullName,
                        remove: () => usersApi.remove(user.id),
                        onDone: reload,
                      })
                  : undefined
              }
            >
              <div className="row">
                <Avatar user={user} size={40} />
                <div className="row row--wrap">
                  <IonChip>{t(`enums.role.${user.role}`)}</IonChip>
                  {user.role === 'client' && (
                    <IonChip
                      color={STATUS_STYLE[user.status].color}
                      outline
                      data-testid="user-status"
                      data-status={user.status}
                    >
                      <IonIcon icon={STATUS_STYLE[user.status].icon} aria-hidden="true" />
                      <IonLabel>{t(`enums.userStatus.${user.status}`)}</IonLabel>
                    </IonChip>
                  )}
                </div>
              </div>
              <PlanChips user={user} />
            </ManagementCard>
          ))}
        </div>
      )}
    </PageLayout>
  );
};

export default UsersPage;
