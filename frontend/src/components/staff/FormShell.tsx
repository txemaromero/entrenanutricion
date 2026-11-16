import { IonButton, IonIcon, IonText } from '@ionic/react';
import { arrowDown, arrowUp, closeCircle } from 'ionicons/icons';
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { errorMessage } from '../../utils/errors';

/** Cancel (red) / Save (green) footer and general error of management forms. */
export const FormActions = ({
  onCancel,
  saving,
  error,
}: {
  onCancel: () => void;
  saving: boolean;
  error?: unknown;
}) => {
  const { t } = useTranslation();
  return (
    <>
      {Boolean(error) && (
        <IonText color="danger" role="alert">
          <p>{errorMessage(t, error)}</p>
        </IonText>
      )}
      <div className="form-actions">
        <IonButton color="danger" fill="outline" onClick={onCancel} data-testid="form-cancel">
          {t('common.cancel')}
        </IonButton>
        <IonButton type="submit" color="primary" disabled={saving} data-testid="form-save">
          {t('common.save')}
        </IonButton>
      </div>
    </>
  );
};

/** Move up / down / remove buttons for rows of ordered lists. */
export const RowControls = ({
  index,
  count,
  onMove,
  onRemove,
  label,
}: {
  index: number;
  count: number;
  onMove: (from: number, to: number) => void;
  onRemove: (index: number) => void;
  label: string;
}) => {
  const { t } = useTranslation();
  return (
    <div className="row">
      <IonButton
        fill="clear"
        className="icon-button"
        disabled={index === 0}
        onClick={() => onMove(index, index - 1)}
        aria-label={t('staff.moveUp', { item: label })}
      >
        <IonIcon slot="icon-only" icon={arrowUp} aria-hidden="true" />
      </IonButton>
      <IonButton
        fill="clear"
        className="icon-button"
        disabled={index === count - 1}
        onClick={() => onMove(index, index + 1)}
        aria-label={t('staff.moveDown', { item: label })}
      >
        <IonIcon slot="icon-only" icon={arrowDown} aria-hidden="true" />
      </IonButton>
      <IonButton
        fill="clear"
        color="danger"
        className="icon-button"
        onClick={() => onRemove(index)}
        aria-label={t('staff.removeRow', { item: label })}
        data-testid={`remove-row-${index}`}
      >
        <IonIcon slot="icon-only" icon={closeCircle} aria-hidden="true" />
      </IonButton>
    </div>
  );
};

export const FormSection = ({ title, children }: { title: string; children: ReactNode }) => (
  <section className="stack">
    <h2 className="section-title">{title}</h2>
    {children}
  </section>
);
