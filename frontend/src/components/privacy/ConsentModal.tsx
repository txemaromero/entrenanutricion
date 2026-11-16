import {
  IonButton,
  IonCheckbox,
  IonContent,
  IonHeader,
  IonModal,
  IonText,
  IonTitle,
  IonToolbar,
} from '@ionic/react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { meApi } from '../../api/me';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { errorMessage } from '../../utils/errors';

/**
 * Blocking consent screen: shown while the user has not accepted the current privacy policy
 * (a new version, or an account created by an admin). Clients also give the explicit consent
 * for health data. The only other way out is logging out.
 */
export const ConsentModal = () => {
  const { t } = useTranslation();
  const { user, setUser, logout } = useAuth();
  const [privacy, setPrivacy] = useState(false);
  const [health, setHealth] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<unknown>();
  if (!user?.consentRequired) return null;
  const isClient = user.role === 'client';

  const accept = async () => {
    setSaving(true);
    setError(undefined);
    try {
      setUser(await meApi.consent({ privacyPolicy: privacy, healthData: isClient && health }));
    } catch (failure) {
      setError(failure);
    } finally {
      setSaving(false);
    }
  };

  return (
    <IonModal isOpen backdropDismiss={false} data-testid="consent-modal">
      <IonHeader>
        <IonToolbar>
          <IonTitle>{t('consent.title')}</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <div className="stack">
          <p>{t('consent.intro')}</p>
          <a href={PATHS.privacy} target="_blank" rel="noreferrer">
            {t('consent.readPolicy')}
          </a>
          <IonCheckbox
            checked={privacy}
            onIonChange={(event) => setPrivacy(event.detail.checked)}
            labelPlacement="end"
            justify="start"
            className="checkbox-wrap"
            data-testid="consent-privacy"
          >
            {t('consent.privacy')}
          </IonCheckbox>
          {isClient && (
            <IonCheckbox
              checked={health}
              onIonChange={(event) => setHealth(event.detail.checked)}
              labelPlacement="end"
              justify="start"
              className="checkbox-wrap"
              data-testid="consent-health"
            >
              {t('consent.health')}
            </IonCheckbox>
          )}
          {Boolean(error) && (
            <IonText color="danger" role="alert">
              <p>{errorMessage(t, error)}</p>
            </IonText>
          )}
          <IonButton
            expand="block"
            disabled={saving || !privacy || (isClient && !health)}
            onClick={() => void accept()}
            data-testid="consent-accept"
          >
            {t('consent.accept')}
          </IonButton>
          <IonButton expand="block" fill="clear" color="medium" onClick={() => void logout()}>
            {t('common.logout')}
          </IonButton>
        </div>
      </IonContent>
    </IonModal>
  );
};
