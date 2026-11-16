import { useIonAlert } from '@ionic/react';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

interface ConfirmOptions {
  header: string;
  message: string;
  confirmText?: string;
  destructive?: boolean;
}

/** Promise-based confirmation dialog (IonAlert) used before deletes, assignments, etc. */
export const useConfirm = () => {
  const [present] = useIonAlert();
  const { t } = useTranslation();

  return useCallback(
    ({ header, message, confirmText, destructive }: ConfirmOptions) =>
      new Promise<boolean>((resolve) => {
        void present({
          header,
          message,
          backdropDismiss: true,
          onDidDismiss: (event) => resolve(event.detail.role === 'confirm'),
          buttons: [
            { text: t('common.cancel'), role: 'cancel' },
            {
              text: confirmText ?? t('common.confirm'),
              role: 'confirm',
              cssClass: destructive ? 'alert-button-danger' : 'alert-button-confirm',
            },
          ],
        });
      }),
    [present, t],
  );
};
