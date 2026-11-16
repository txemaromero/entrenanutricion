import { IonButton, IonIcon, IonSpinner, IonText } from '@ionic/react';
import { checkmarkCircleOutline } from 'ionicons/icons';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';

import { authApi } from '../../api/auth';
import { ApiError } from '../../api/errors';
import { meApi } from '../../api/me';
import { PATHS, homePath } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { errorMessage } from '../../utils/errors';

type State = { kind: 'checking' } | { kind: 'verified' } | { kind: 'failed'; error: unknown };

/** Open link of the verification email (`/verify-email?token=…`), signed in or not. */
const VerifyEmailPage = () => {
  const { t } = useTranslation();
  const { search } = useLocation();
  const { user, refreshUser } = useAuth();
  // Ionic keeps the page mounted after leaving it: read the token once, from the URL it opened.
  const [token] = useState(() => new URLSearchParams(search).get('token') ?? '');
  const [state, setState] = useState<State>({ kind: 'checking' });
  const [resent, setResent] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const verify = async () => {
      try {
        if (!token) throw new ApiError({ status: 400, code: 'verification_link_invalid' });
        await authApi.verifyEmail(token);
        if (!cancelled) setState({ kind: 'verified' });
        await refreshUser().catch(() => null); // signed in: the banner goes away
      } catch (error) {
        if (!cancelled) setState({ kind: 'failed', error });
      }
    };
    void verify();
    return () => {
      cancelled = true;
    };
  }, [token, refreshUser]);

  const resend = async () => {
    await meApi.resendVerification().catch(() => undefined);
    setResent(true);
  };

  const continueTo = user ? homePath(user) : PATHS.login;

  return (
    <PageLayout title={t('verifyEmail.title')} narrow hideEmailReminder>
      <div className="stack" style={{ alignItems: 'center', textAlign: 'center' }}>
        {state.kind === 'checking' && (
          <>
            <IonSpinner name="dots" color="primary" aria-hidden="true" />
            <p role="status">{t('verifyEmail.checking')}</p>
          </>
        )}
        {state.kind === 'verified' && (
          <>
            <IonIcon
              icon={checkmarkCircleOutline}
              color="success"
              style={{ fontSize: 72 }}
              aria-hidden="true"
            />
            <h1 style={{ margin: 0 }} data-testid="email-verified">
              {t('verifyEmail.verified')}
            </h1>
            <p className="muted">{t('verifyEmail.verifiedHint')}</p>
            <IonButton routerLink={continueTo} routerDirection="root" data-testid="verify-continue">
              {user ? t('verifyEmail.toApp') : t('verifyEmail.toLogin')}
            </IonButton>
          </>
        )}
        {state.kind === 'failed' && (
          <>
            <IonText color="danger" role="alert" data-testid="verify-failed">
              <p>{errorMessage(t, state.error)}</p>
            </IonText>
            {user && !user.emailVerified && (
              <IonButton
                fill="outline"
                disabled={resent}
                onClick={() => void resend()}
                data-testid="verify-resend"
              >
                {resent ? t('verifyEmail.resent') : t('verifyEmail.resend')}
              </IonButton>
            )}
            <IonButton fill="clear" routerLink={continueTo} routerDirection="root">
              {user ? t('verifyEmail.toApp') : t('verifyEmail.toLogin')}
            </IonButton>
          </>
        )}
      </div>
    </PageLayout>
  );
};

export default VerifyEmailPage;
