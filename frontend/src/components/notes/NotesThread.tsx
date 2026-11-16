import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonIcon, IonText, IonTextarea } from '@ionic/react';
import { sendOutline } from 'ionicons/icons';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import type { Note } from '../../api/types';
import { formatDateTime } from '../../i18n/format';
import { errorMessage, translateKey } from '../../utils/errors';
import { NOTE_MAX_LENGTH, noteSchema, type NoteForm } from '../../validation/notes';

/**
 * Thread of notes between a client and the team, oldest first, with a box to write a new one.
 * The viewer's own side is on the right; notes of the other side not read yet are marked "New".
 */
export const NotesThread = ({
  notes,
  viewer,
  onSend,
}: {
  /** Newest first, as the API returns them. */
  notes: Note[];
  viewer: 'client' | 'staff';
  onSend: (body: string) => Promise<void>;
}) => {
  const { t, i18n } = useTranslation();
  const [sendError, setSendError] = useState<unknown>();
  const { control, handleSubmit, reset, formState } = useForm<NoteForm>({
    resolver: zodResolver(noteSchema),
    defaultValues: { body: '' },
  });
  const mine = (note: Note) => (viewer === 'client' ? note.fromClient : !note.fromClient);
  const author = (note: Note) => {
    if (viewer === 'client' && note.fromClient) return t('notes.you');
    if (note.fromClient) return note.authorName;
    return t('notes.byRole', {
      name: note.authorName,
      role: t(`enums.role.${note.authorRole}`),
    });
  };

  const onSubmit = handleSubmit(async ({ body }) => {
    setSendError(undefined);
    try {
      await onSend(body);
      reset({ body: '' });
    } catch (error) {
      setSendError(error);
    }
  });

  return (
    <div className="stack">
      {notes.length === 0 ? (
        <p className="muted" style={{ margin: 0 }} data-testid="notes-empty">
          {viewer === 'client' ? t('notes.emptyClient') : t('notes.emptyStaff')}
        </p>
      ) : (
        <ol className="notes-thread" aria-label={t('notes.thread')} data-testid="notes-thread">
          {[...notes].reverse().map((note) => (
            <li
              key={note.id}
              className={mine(note) ? 'note note--mine' : 'note'}
              data-testid={`note-${note.id}`}
              data-mine={mine(note)}
            >
              <span className="note__meta">
                {author(note)} · {formatDateTime(note.createdAt, i18n.language)}
                {!mine(note) && note.readAt === null && (
                  <strong className="note__new" data-testid="note-new">
                    {' '}
                    · {t('notes.new')}
                  </strong>
                )}
              </span>
              <p className="note__body">{note.body}</p>
            </li>
          ))}
        </ol>
      )}
      <form className="stack" onSubmit={onSubmit} noValidate>
        <Controller
          control={control}
          name="body"
          render={({ field, fieldState }) => {
            const error = translateKey(t, fieldState.error?.message);
            return (
              <IonTextarea
                label={t('notes.write')}
                labelPlacement="floating"
                fill="outline"
                autoGrow
                rows={3}
                counter
                maxlength={NOTE_MAX_LENGTH}
                value={field.value}
                errorText={error}
                className={error ? 'ion-invalid ion-touched' : undefined}
                aria-invalid={error ? true : undefined}
                onIonInput={(event) => field.onChange(event.detail.value ?? '')}
                onIonBlur={field.onBlur}
                data-testid="note-body"
              />
            );
          }}
        />
        {Boolean(sendError) && (
          <IonText color="danger" role="alert">
            <small>{errorMessage(t, sendError)}</small>
          </IonText>
        )}
        <IonButton
          type="submit"
          disabled={formState.isSubmitting}
          style={{ alignSelf: 'flex-end' }}
          data-testid="send-note"
        >
          <IonIcon slot="start" icon={sendOutline} aria-hidden="true" />
          {t('notes.send')}
        </IonButton>
      </form>
    </div>
  );
};
