import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonContent,
  IonHeader,
  IonIcon,
  IonInput,
  IonModal,
  IonText,
  IonTitle,
  IonToolbar,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { downloadOutline, shieldCheckmarkOutline, trashOutline } from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { meApi } from '../../api/me';
import type { Me } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { apiFieldError, errorMessage } from '../../utils/errors';

const saveFile = (blob: Blob, name: string) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
};

/** Profile › Privacy and data: policy, data export and (clients) account deletion. */
export const PrivacyCard = ({ user }: { user: Me }) => {
  const { t } = useTranslation();
  const router = useIonRouter();
  const [toast] = useIonToast();
  const { logout } = useAuth();
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<unknown>();

  const exportData = async () => {
    setExporting(true);
    try {
      const { blob, filename } = await meApi.exportData();
      saveFile(blob, filename);
      void toast({ message: t('profile.privacy.exported'), duration: 2000, color: 'success' });
    } catch (failure) {
      void toast({ message: errorMessage(t, failure), duration: 3000, color: 'danger' });
    } finally {
      setExporting(false);
    }
  };

  const deleteAccount = async () => {
    setError(undefined);
    try {
      await meApi.deleteAccount(password);
      setDeleting(false);
      await logout();
      void toast({ message: t('profile.privacy.deleted'), duration: 3000, color: 'success' });
      router.push(PATHS.welcome, 'root', 'replace');
    } catch (failure) {
      setError(failure);
    }
  };

  const closeDelete = () => {
    setDeleting(false);
    setPassword('');
    setError(undefined);
  };
  const passwordError = apiFieldError(t, error, 'password');

  return (
    <IonCard data-testid="privacy-card">
      <IonCardHeader>
        <IonCardTitle>{t('profile.privacy.title')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent className="stack">
        <IonButton fill="outline" routerLink={PATHS.privacy} data-testid="privacy-policy-link">
          <IonIcon slot="start" icon={shieldCheckmarkOutline} aria-hidden="true" />
          {t('profile.privacy.policy')}
        </IonButton>
        <IonButton
          fill="outline"
          disabled={exporting}
          onClick={() => void exportData()}
          data-testid="privacy-export"
        >
          <IonIcon slot="start" icon={downloadOutline} aria-hidden="true" />
          {t('profile.privacy.export')}
        </IonButton>
        {user.role === 'client' && (
          <IonButton
            color="danger"
            fill="clear"
            onClick={() => setDeleting(true)}
            data-testid="privacy-delete"
          >
            <IonIcon slot="start" icon={trashOutline} aria-hidden="true" />
            {t('profile.privacy.delete')}
          </IonButton>
        )}
      </IonCardContent>

      <IonModal isOpen={deleting} onDidDismiss={closeDelete} data-testid="delete-account-modal">
        <IonHeader>
          <IonToolbar>
            <IonTitle>{t('profile.privacy.deleteTitle')}</IonTitle>
          </IonToolbar>
        </IonHeader>
        <IonContent className="ion-padding">
          <form
            className="stack"
            noValidate
            onSubmit={(event) => {
              event.preventDefault();
              void deleteAccount();
            }}
          >
            <IonText color="danger">
              <p>{t('profile.privacy.deleteWarning')}</p>
            </IonText>
            <IonInput
              type="password"
              label={t('profile.privacy.deletePassword')}
              labelPlacement="floating"
              fill="outline"
              autocomplete="current-password"
              value={password}
              onIonInput={(event) => setPassword(String(event.detail.value ?? ''))}
              data-testid="delete-password"
            />
            {(passwordError || (Boolean(error) && !passwordError)) && (
              <IonText color="danger" role="alert">
                <small>{passwordError ?? errorMessage(t, error)}</small>
              </IonText>
            )}
            <div className="form-actions">
              <IonButton fill="outline" onClick={closeDelete}>
                {t('common.cancel')}
              </IonButton>
              <IonButton
                type="submit"
                color="danger"
                disabled={!password}
                data-testid="delete-confirm"
              >
                {t('profile.privacy.deleteConfirm')}
              </IonButton>
            </div>
          </form>
        </IonContent>
      </IonModal>
    </IonCard>
  );
};
