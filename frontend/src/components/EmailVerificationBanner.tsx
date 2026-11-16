import { IonButton, IonIcon, IonText, useIonToast } from '@ionic/react';
import { mailUnreadOutline } from 'ionicons/icons';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

import { meApi } from '../api/me';
import { useAuth } from '../auth/useAuth';
import { errorMessage } from '../utils/errors';

/** Signed in with an address not confirmed yet: reminder and a button to get the link again. */
export const EmailVerificationBanner = () => {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [toast] = useIonToast();
  const [sending, setSending] = useState(false);
  if (!user || user.emailVerified) return null;

  const resend = async () => {
    setSending(true);
    try {
      await meApi.resendVerification();
      void toast({ message: t('verifyEmail.resent'), duration: 3000, color: 'success' });
    } catch (error) {
      void toast({ message: errorMessage(t, error), duration: 3000, color: 'danger' });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="verify-banner" role="status" data-testid="verify-email-banner">
      <IonIcon icon={mailUnreadOutline} aria-hidden="true" />
      <IonText>{t('verifyEmail.banner', { email: user.email })}</IonText>
      <IonButton
        size="small"
        fill="outline"
        disabled={sending}
        onClick={() => void resend()}
        data-testid="resend-verification"
      >
        {t('verifyEmail.resend')}
      </IonButton>
    </div>
  );
};
