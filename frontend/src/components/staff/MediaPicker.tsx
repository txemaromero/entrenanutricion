import { IonButton, IonIcon, IonText } from '@ionic/react';
import { cloudUploadOutline, trashOutline } from 'ionicons/icons';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import type { MediaKind } from '../../api/types';
import { checkMediaFile, MEDIA_ACCEPT, mediaKindOf } from '../../utils/media';

export interface MediaChange {
  file?: File;
  remove: boolean;
}

/** Single image or video: upload, replace or remove (applied when the form is saved). */
export const MediaPicker = ({
  currentUrl,
  currentKind,
  value,
  onChange,
  label,
  serverError,
}: {
  currentUrl: string | null;
  currentKind: MediaKind | null;
  value: MediaChange;
  onChange: (change: MediaChange) => void;
  label: string;
  /** The API refused the file when the form was saved. */
  serverError?: string;
}) => {
  const { t } = useTranslation();
  const input = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string>();
  const preview = useMemo(
    () => (value.file ? URL.createObjectURL(value.file) : undefined),
    [value.file],
  );
  useEffect(() => () => (preview ? URL.revokeObjectURL(preview) : undefined), [preview]);

  const shownUrl = preview ?? (value.remove ? null : currentUrl);
  const shownKind = value.file ? mediaKindOf(value.file) : currentKind;

  const pick = (file?: File) => {
    if (!file) return;
    const problem = checkMediaFile(file);
    setError(problem ? t(problem) : undefined);
    if (!problem) onChange({ file, remove: false });
  };

  return (
    <fieldset className="choice-fieldset">
      <legend>{label}</legend>
      {shownUrl &&
        (shownKind === 'video' ? (
          <video src={shownUrl} controls style={{ width: '100%', borderRadius: 12 }} />
        ) : (
          <img
            src={shownUrl}
            alt=""
            style={{ width: '100%', maxHeight: 220, objectFit: 'cover', borderRadius: 12 }}
          />
        ))}
      <input
        ref={input}
        type="file"
        accept={MEDIA_ACCEPT}
        hidden
        onChange={(event) => pick(event.target.files?.[0])}
        data-testid="media-input"
      />
      <div className="row row--wrap">
        <IonButton fill="outline" size="small" onClick={() => input.current?.click()}>
          <IonIcon slot="start" icon={cloudUploadOutline} aria-hidden="true" />
          {shownUrl ? t('staff.changeMedia') : t('staff.uploadMedia')}
        </IonButton>
        {shownUrl && (
          <IonButton
            fill="outline"
            size="small"
            color="danger"
            onClick={() => onChange({ file: undefined, remove: Boolean(currentUrl) })}
          >
            <IonIcon slot="start" icon={trashOutline} aria-hidden="true" />
            {t('staff.removeMedia')}
          </IonButton>
        )}
      </div>
      {(error ?? serverError) && (
        <IonText color="danger" role="alert" data-testid="media-error">
          <small>{error ?? serverError}</small>
        </IonText>
      )}
    </fieldset>
  );
};
