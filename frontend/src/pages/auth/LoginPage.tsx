import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonCheckbox, IonRouterLink, IonText } from '@ionic/react';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useHistory, useLocation } from 'react-router-dom';

import { useAuth } from '../../auth/useAuth';
import { PATHS, homePath } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { TextField } from '../../components/form/TextField';
import { errorMessage } from '../../utils/errors';
import { loginSchema, type LoginForm } from '../../validation/schemas';

const LoginPage = () => {
  const { t } = useTranslation();
  const history = useHistory();
  const { search } = useLocation();
  const passwordReset = new URLSearchParams(search).has('passwordReset');
  const { login, sessionExpired } = useAuth();
  const [submitError, setSubmitError] = useState<string>();

  const { control, handleSubmit, formState } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '', rememberMe: false },
  });

  const onSubmit = handleSubmit(async ({ email, password, rememberMe }) => {
    setSubmitError(undefined);
    try {
      const user = await login(email, password, rememberMe);
      history.replace(homePath(user));
    } catch (error) {
      setSubmitError(errorMessage(t, error));
    }
  });

  return (
    <PageLayout title={t('auth.login.title')} backHref={PATHS.welcome} narrow>
      <form className="stack" onSubmit={onSubmit} noValidate>
        {passwordReset && !submitError && (
          <IonText color="success" role="status" data-testid="password-reset-done">
            <p>{t('auth.login.passwordResetDone')}</p>
          </IonText>
        )}
        {sessionExpired && !passwordReset && !submitError && (
          <IonText color="medium">
            <p>{t('auth.sessionExpired')}</p>
          </IonText>
        )}
        <TextField
          control={control}
          name="email"
          label={t('auth.login.email')}
          type="email"
          inputMode="email"
          autocomplete="email"
        />
        <TextField
          control={control}
          name="password"
          label={t('auth.login.password')}
          type="password"
          autocomplete="current-password"
          revealable
        />
        <IonRouterLink
          routerLink={PATHS.forgotPassword}
          className="forgot-password-link"
          data-testid="forgot-password-link"
        >
          {t('auth.login.forgotPassword')}
        </IonRouterLink>
        <Controller
          control={control}
          name="rememberMe"
          render={({ field }) => (
            <IonCheckbox
              checked={field.value}
              onIonChange={(event) => field.onChange(event.detail.checked)}
              labelPlacement="end"
              justify="start"
              data-testid="field-rememberMe"
            >
              {t('auth.login.rememberMe')}
            </IonCheckbox>
          )}
        />
        {submitError && (
          <IonText color="danger" role="alert" data-testid="login-error">
            <p>{submitError}</p>
          </IonText>
        )}
        <IonButton
          type="submit"
          expand="block"
          disabled={formState.isSubmitting}
          data-testid="login-submit"
        >
          {t('auth.login.submit')}
        </IonButton>
        <p style={{ textAlign: 'center' }}>
          {t('auth.login.noAccount')}{' '}
          <IonRouterLink routerLink={PATHS.register}>{t('auth.login.registerLink')}</IonRouterLink>
        </p>
      </form>
    </PageLayout>
  );
};

export default LoginPage;
