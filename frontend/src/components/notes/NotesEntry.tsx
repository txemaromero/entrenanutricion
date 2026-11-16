import { IonBadge, IonCard, IonCardContent, IonIcon } from '@ionic/react';
import { chatbubblesOutline } from 'ionicons/icons';
import { useTranslation } from 'react-i18next';

import { notesApi } from '../../api/client-features';
import { PATHS } from '../../auth/routing';
import { useResource } from '../../hooks/useResource';

/** Client: link to the notes with the team, with the count of new ones. */
export const NotesEntry = ({ onlyUnread = false }: { onlyUnread?: boolean }) => {
  const { t } = useTranslation();
  // Without a connection there is nothing to show: the notes need the network.
  const { data: unread } = useResource(notesApi.unread);
  if (unread === undefined || (onlyUnread && unread === 0)) return null;

  return (
    <IonCard button routerLink={PATHS.notes} data-testid="notes-entry" data-unread={unread}>
      <IonCardContent className="row">
        <IonIcon
          icon={chatbubblesOutline}
          color="primary"
          style={{ fontSize: 28, flexShrink: 0 }}
          aria-hidden="true"
        />
        <span style={{ flex: 1 }}>
          <strong style={{ display: 'block' }}>{t('notes.title')}</strong>
          <small className="muted">
            {unread ? t('notes.unread', { count: unread }) : t('notes.entryHint')}
          </small>
        </span>
        {unread > 0 && (
          <IonBadge color="danger" aria-hidden="true">
            {unread}
          </IonBadge>
        )}
      </IonCardContent>
    </IonCard>
  );
};
