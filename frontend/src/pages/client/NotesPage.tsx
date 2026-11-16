import { useIonToast } from '@ionic/react';
import { useTranslation } from 'react-i18next';

import { notesApi } from '../../api/client-features';
import { PATHS } from '../../auth/routing';
import { NotesThread } from '../../components/notes/NotesThread';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { useResource } from '../../hooks/useResource';

/** Opening the thread marks the team's notes as read (they still show "New" this time). */
const loadNotes = async () => {
  const page = await notesApi.list();
  if (page.results.some((note) => !note.fromClient && note.readAt === null)) {
    void notesApi.markRead().catch(() => undefined);
  }
  return page;
};

/** Client: asynchronous notes with the trainer and the nutritionist. */
const NotesPage = () => {
  const { t } = useTranslation();
  const [toast] = useIonToast();
  const { data, error, loading, reload, setData } = useResource(loadNotes);

  const send = async (body: string) => {
    const note = await notesApi.send(body);
    if (data) setData({ ...data, count: data.count + 1, results: [note, ...data.results] });
    void toast({ message: t('notes.sent'), duration: 2000, color: 'success' });
  };

  return (
    <PageLayout title={t('notes.title')} backHref={PATHS.profile} onRefresh={reload} narrow>
      <div className="stack">
        <p className="muted" style={{ margin: 0 }}>
          {t('notes.intro')}
        </p>
        {loading && !data && <ListSkeleton rows={2} />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && <NotesThread notes={data.results} viewer="client" onSend={send} />}
      </div>
    </PageLayout>
  );
};

export default NotesPage;
