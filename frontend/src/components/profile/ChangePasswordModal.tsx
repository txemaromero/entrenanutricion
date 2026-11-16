import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonContent,
  IonHeader,
  IonModal,
  IonText,
  IonTitle,
  IonToolbar,
  useIonToast,
} from '@ionic/react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { ApiError } from '../../api/errors';
import { meApi } from '../../api/me';
import { tokens } from '../../api/tokens';
import { apiFieldError, errorMessage } from '../../utils/errors';
import { passwordChangeSchema, type PasswordChangeForm } from '../../validation/schemas';
import { TextField } from '../form/TextField';

const EMPTY: PasswordChangeForm = { currentPassword: '', newPassword: '', confirmPassword: '' };

/** Change password (US-12). The backend returns a fresh token pair for this session. */
export const ChangePasswordModal = ({
  isOpen,
  onClose,
}: {
  isOpen: boolean;
  onClose: () => void;
}) => {
  const { t } = useTranslation();
  const [toast] = useIonToast();
  const [submitError, setSubmitError] = useState<unknown>();
  const { control, handleSubmit, reset, formState } = useForm<PasswordChangeForm>({
    resolver: zodResolver(passwordChangeSchema),
    defaultValues: EMPTY,
  });

  const close = () => {
    reset(EMPTY);
    setSubmitError(undefined);
    onClose();
  };

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(undefined);
    try {
      tokens.startSession((await meApi.changePassword(values)).access);
      void toast({ message: t('profile.passwordChanged'), duration: 2500, color: 'success' });
      close();
    } catch (error) {
      setSubmitError(error);
    }
  });

  const fieldError = (field: string) => apiFieldError(t, submitError, field);
  const generalError =
    Boolean(submitError) &&
    !(submitError instanceof ApiError && Object.keys(submitError.fieldCodes).length > 0);

  return (
    <IonModal isOpen={isOpen} onDidDismiss={close} data-testid="password-modal">
      <IonHeader>
        <IonToolbar>
          <IonTitle>{t('profile.changePassword')}</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent className="ion-padding">
        <form className="stack" onSubmit={onSubmit} noValidate>
          <TextField
            control={control}
            name="currentPassword"
            label={t('profile.currentPassword')}
            type="password"
            autocomplete="current-password"
            revealable
            required
            serverError={fieldError('currentPassword')}
          />
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
          <div className="form-actions">
            <IonButton color="danger" fill="outline" onClick={close} data-testid="password-cancel">
              {t('common.cancel')}
            </IonButton>
            <IonButton
              type="submit"
              disabled={formState.isSubmitting}
              data-testid="password-confirm"
            >
              {t('common.confirm')}
            </IonButton>
          </div>
        </form>
      </IonContent>
    </IonModal>
  );
};
