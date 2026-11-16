import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonText } from '@ionic/react';
import { useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useHistory, useLocation } from 'react-router-dom';

import { authApi } from '../../api/auth';
import { ApiError } from '../../api/errors';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { TextField } from '../../components/form/TextField';
import { PasswordRequirements } from '../../components/form/fields';
import { apiFieldError, errorMessage } from '../../utils/errors';
import { resetPasswordSchema, type ResetPasswordForm } from '../../validation/schemas';

const readLink = (search: string) => {
  const params = new URLSearchParams(search);
  return { uid: params.get('uid') ?? '', token: params.get('token') ?? '' };
};

/** Choose a new password from the emailed link (`/reset-password?uid=…&token=…`). */
const ResetPasswordPage = () => {
  const { t } = useTranslation();
  const history = useHistory();
  const { search } = useLocation();
  // Ionic keeps the page mounted after leaving it: read the link once, from the URL it opened.
  const [link] = useState(() => readLink(search));
  const [submitError, setSubmitError] = useState<unknown>();
  const { control, handleSubmit, formState } = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { newPassword: '', confirmPassword: '' },
  });
  const newPassword = useWatch({ control, name: 'newPassword' });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(undefined);
    try {
      await authApi.confirmPasswordReset({ ...link, ...values });
      history.replace(`${PATHS.login}?passwordReset=1`);
    } catch (error) {
      setSubmitError(error);
    }
  });

  const linkInvalid =
    !link.uid ||
    !link.token ||
    (submitError instanceof ApiError && submitError.code === 'reset_link_invalid');
  const fieldError = (field: string) => apiFieldError(t, submitError, field);
  const generalError =
    Boolean(submitError) &&
    !(submitError instanceof ApiError && Object.keys(submitError.fieldCodes).length > 0);

  return (
    <PageLayout title={t('auth.reset.title')} backHref={PATHS.login} narrow>
      {linkInvalid ? (
        <div className="stack">
          <IonText color="danger" role="alert" data-testid="reset-invalid">
            <p>{t('errors.reset_link_invalid')}</p>
          </IonText>
          <IonButton expand="block" routerLink={PATHS.forgotPassword} routerDirection="forward">
            {t('auth.reset.requestNew')}
          </IonButton>
        </div>
      ) : (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <p>{t('auth.reset.intro')}</p>
          <TextField
            control={control}
            name="newPassword"
            label={t('profile.newPassword')}
            type="password"
            autocomplete="new-password"
            revealable
            required
            serverError={fieldError('newPassword')}
          />
          <PasswordRequirements value={newPassword} />
          <TextField
            control={control}
            name="confirmPassword"
            label={t('profile.confirmPassword')}
            type="password"
            autocomplete="new-password"
            revealable
            required
            serverError={fieldError('confirmPassword')}
          />
          {generalError && (
            <IonText color="danger" role="alert">
              <p>{errorMessage(t, submitError)}</p>
            </IonText>
          )}
          <IonButton
            type="submit"
            expand="block"
            disabled={formState.isSubmitting}
            data-testid="reset-submit"
          >
            {t('auth.reset.submit')}
          </IonButton>
        </form>
      )}
    </PageLayout>
  );
};

export default ResetPasswordPage;
