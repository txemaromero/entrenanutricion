import {
  IonBadge,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonItem,
  IonLabel,
  IonList,
  useIonToast,
} from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { staffNotesApi } from '../../api/staff';
import { PATHS } from '../../auth/routing';
import { useResource } from '../../hooks/useResource';
import { formatDateTime } from '../../i18n/format';
import { ErrorState, ListSkeleton } from '../States';
import { Avatar } from '../staff/UserProfileBlocks';
import { NotesThread } from './NotesThread';

/** User profile (staff): the client's thread; opening it marks the client's notes as read. */
export const ClientNotesCard = ({ userId }: { userId: number }) => {
  const { t } = useTranslation();
  const [toast] = useIonToast();
  // Notes of the client still unread when this profile was opened: they keep their "new" mark
  // during the visit, also when the thread is loaded again after they were marked as read.
  const [unread, setUnread] = useState<{ userId: number; ids: number[] }>({ userId, ids: [] });
  const { data, error, reload, setData } = useResource(async () => {
    const page = await staffNotesApi.list(userId);
    const fresh = page.results.filter((note) => note.fromClient && note.readAt === null);
    if (fresh.length > 0) {
      setUnread((previous) => ({
        userId,
        ids: [...(previous.userId === userId ? previous.ids : []), ...fresh.map((note) => note.id)],
      }));
      void staffNotesApi.markRead(userId).catch(() => undefined);
    }
    return page;
  }, [userId]);
  const unreadIds = unread.userId === userId ? unread.ids : [];
  const notes = data?.results.map((note) =>
    unreadIds.includes(note.id) ? { ...note, readAt: null } : note,
  );

  const send = async (body: string) => {
    const note = await staffNotesApi.send(userId, body);
    if (data) setData({ ...data, count: data.count + 1, results: [note, ...data.results] });
    void toast({ message: t('notes.sent'), duration: 2000, color: 'success' });
  };

  return (
    <IonCard data-testid="client-notes">
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{t('notes.staffTitle')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent>
        {data ? (
          <NotesThread notes={notes ?? []} viewer="staff" onSend={send} />
        ) : error ? (
          <ErrorState error={error} onRetry={reload} />
        ) : (
          <ListSkeleton rows={1} />
        )}
      </IonCardContent>
    </IonCard>
  );
};

/** Users page (staff): clients waiting for an answer, the most recent first. */
export const NotesInboxCard = () => {
  const { t, i18n } = useTranslation();
  const { data } = useResource(staffNotesApi.inbox);
  if (!data || data.length === 0) return null;

  return (
    <IonCard data-testid="notes-inbox">
      <IonCardHeader>
        <IonCardTitle style={{ fontSize: '1.1rem' }}>{t('notes.inboxTitle')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent>
        <IonList lines="full">
          {data.map((entry) => (
            <IonItem
              key={entry.client.id}
              button
              detail
              routerLink={`${PATHS.users}/${entry.client.id}`}
              data-testid={`inbox-${entry.client.id}`}
            >
              <span slot="start">
                <Avatar user={entry.client} size={36} />
              </span>
              <IonLabel>
                <h3>{entry.client.fullName}</h3>
                <p className="line-clamp-2">{entry.lastNote}</p>
                <p>{formatDateTime(entry.lastNoteAt, i18n.language)}</p>
              </IonLabel>
              <IonBadge slot="end" color="danger">
                {t('notes.inboxUnread', { count: entry.unread })}
              </IonBadge>
            </IonItem>
          ))}
        </IonList>
      </IonCardContent>
    </IonCard>
  );
};
