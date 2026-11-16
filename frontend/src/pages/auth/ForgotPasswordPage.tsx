import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonText } from '@ionic/react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { authApi } from '../../api/auth';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { TextField } from '../../components/form/TextField';
import { errorMessage } from '../../utils/errors';
import { forgotPasswordSchema, type ForgotPasswordForm } from '../../validation/schemas';

/** Request a password reset link. The answer is the same whether or not the account exists. */
const ForgotPasswordPage = () => {
  const { t } = useTranslation();
  const [sentTo, setSentTo] = useState<string>();
  const [submitError, setSubmitError] = useState<string>();
  const { control, handleSubmit, formState } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  });

  const onSubmit = handleSubmit(async ({ email }) => {
    setSubmitError(undefined);
    try {
      await authApi.requestPasswordReset(email);
      setSentTo(email);
    } catch (error) {
      setSubmitError(errorMessage(t, error));
    }
  });

  return (
    <PageLayout title={t('auth.forgot.title')} backHref={PATHS.login} narrow>
      {sentTo ? (
        <div className="stack">
          <IonText role="status" data-testid="forgot-sent">
            <p>{t('auth.forgot.sent', { email: sentTo })}</p>
          </IonText>
          <IonButton expand="block" routerLink={PATHS.login} routerDirection="back">
            {t('auth.forgot.backToLogin')}
          </IonButton>
        </div>
      ) : (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <p>{t('auth.forgot.intro')}</p>
          <TextField
            control={control}
            name="email"
            label={t('auth.login.email')}
            type="email"
            inputMode="email"
            autocomplete="email"
            required
          />
          {submitError && (
            <IonText color="danger" role="alert">
              <p>{submitError}</p>
            </IonText>
          )}
          <IonButton
            type="submit"
            expand="block"
            disabled={formState.isSubmitting}
            data-testid="forgot-submit"
          >
            {t('auth.forgot.submit')}
          </IonButton>
        </form>
      )}
    </PageLayout>
  );
};

export default ForgotPasswordPage;
