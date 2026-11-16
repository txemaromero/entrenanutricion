import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonButtons,
  IonCheckbox,
  IonContent,
  IonHeader,
  IonModal,
  IonText,
  IonTitle,
  IonToolbar,
} from '@ionic/react';
import { useMemo, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useHistory } from 'react-router-dom';

import { authApi } from '../../api/auth';
import { ApiError } from '../../api/errors';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { PasswordRequirements, SelectField } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { apiFieldError, errorMessage } from '../../utils/errors';
import {
  displayDateToIso,
  emailSchema,
  maskDisplayDate,
  registerSchema,
  type RegisterForm,
} from '../../validation/schemas';

const RegisterPage = () => {
  const { t } = useTranslation();
  const history = useHistory();
  const { register: registerUser } = useAuth();
  const [termsOpen, setTermsOpen] = useState(false);
  const [emailTaken, setEmailTaken] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>();
  const schema = useMemo(() => registerSchema(), []);

  const { control, handleSubmit, formState, setError } = useForm<RegisterForm>({
    resolver: zodResolver(schema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      password: '',
      birthDate: '',
      gender: undefined,
      termsAccepted: false,
      healthDataConsent: false,
    },
  });
  const password = useWatch({ control, name: 'password' });

  const checkEmail = async (value: unknown) => {
    const email = String(value ?? '');
    if (!emailSchema.safeParse(email).success) return;
    try {
      const exists = await authApi.emailExists(email.trim());
      setEmailTaken(exists);
      if (exists) setError('email', { type: 'server', message: 'errors.email_taken' });
    } catch {
      setEmailTaken(false);
    }
  };

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(undefined);
    try {
      await registerUser({
        firstName: values.firstName.trim(),
        lastName: values.lastName.trim(),
        email: values.email.trim(),
        password: values.password,
        birthDate: displayDateToIso(values.birthDate)!,
        gender: values.gender,
        termsAccepted: true,
        healthDataConsent: true,
      });
      history.replace(PATHS.onboarding);
    } catch (error) {
      setSubmitError(error);
      if (error instanceof ApiError && error.fieldCodes.email?.includes('email_taken')) {
        setEmailTaken(true);
      }
    }
  });

  const serverError = (field: string) => apiFieldError(t, submitError, field);
  const canSubmit = formState.isValid && !emailTaken && !formState.isSubmitting;

  return (
    <PageLayout title={t('auth.register.title')} backHref={PATHS.welcome} narrow>
      <form className="stack" onSubmit={onSubmit} noValidate>
        <TextField
          control={control}
          name="firstName"
          label={t('auth.register.firstName')}
          autocomplete="given-name"
          required
          serverError={serverError('firstName')}
        />
        <TextField
          control={control}
          name="lastName"
          label={t('auth.register.lastName')}
          autocomplete="family-name"
          required
          serverError={serverError('lastName')}
        />
        <TextField
          control={control}
          name="email"
          label={t('auth.login.email')}
          type="email"
          inputMode="email"
          autocomplete="email"
          required
          serverError={serverError('email')}
          parse={(value) => {
            setEmailTaken(false);
            return value;
          }}
          onBlurExtra={checkEmail}
        />
        <TextField
          control={control}
          name="password"
          label={t('auth.login.password')}
          type="password"
          autocomplete="new-password"
          revealable
          required
          serverError={serverError('password')}
        />
        <PasswordRequirements value={password} />
        <TextField
          control={control}
          name="birthDate"
          label={t('auth.register.birthDate')}
          placeholder={t('auth.register.datePlaceholder')}
          inputMode="numeric"
          autocomplete="bday"
          required
          parse={(value) => maskDisplayDate(String(value))}
          serverError={serverError('birthDate')}
        />
        <SelectField
          control={control}
          name="gender"
          label={t('auth.register.gender')}
          required
          options={(['M', 'F', 'O'] as const).map((value) => ({
            value,
            label: t(`enums.gender.${value}`),
          }))}
        />
        <Controller
          control={control}
          name="termsAccepted"
          render={({ field, fieldState }) => (
            <div>
              <IonCheckbox
                checked={Boolean(field.value)}
                onIonChange={(event) => field.onChange(event.detail.checked)}
                labelPlacement="end"
                justify="start"
                className="checkbox-wrap"
                data-testid="field-termsAccepted"
              >
                {t('auth.register.acceptTerms')} *
              </IonCheckbox>
              <IonButton fill="clear" size="small" onClick={() => setTermsOpen(true)}>
                {t('auth.register.readTerms')}
              </IonButton>
              <IonButton fill="clear" size="small" routerLink={PATHS.privacy}>
                {t('auth.register.readPrivacy')}
              </IonButton>
              {fieldState.error && fieldState.isDirty && (
                <IonText color="danger" role="alert">
                  <small>{t('errors.terms_required')}</small>
                </IonText>
              )}
            </div>
          )}
        />
        <Controller
          control={control}
          name="healthDataConsent"
          render={({ field, fieldState }) => (
            <div>
              <IonCheckbox
                checked={Boolean(field.value)}
                onIonChange={(event) => field.onChange(event.detail.checked)}
                labelPlacement="end"
                justify="start"
                className="checkbox-wrap"
                data-testid="field-healthDataConsent"
              >
                {t('auth.register.healthConsent')} *
              </IonCheckbox>
              {fieldState.error && fieldState.isDirty && (
                <IonText color="danger" role="alert">
                  <small>{t('errors.health_consent_required')}</small>
                </IonText>
              )}
            </div>
          )}
        />
        {Boolean(submitError) &&
          !(submitError instanceof ApiError && submitError.status === 400) && (
            <IonText color="danger" role="alert">
              <p>{errorMessage(t, submitError)}</p>
            </IonText>
          )}
        <IonButton type="submit" expand="block" disabled={!canSubmit} data-testid="register-submit">
          {t('auth.register.submit')}
        </IonButton>
      </form>

      <IonModal isOpen={termsOpen} onDidDismiss={() => setTermsOpen(false)}>
        <IonHeader>
          <IonToolbar>
            <IonTitle>{t('auth.register.termsTitle')}</IonTitle>
            <IonButtons slot="end">
              <IonButton onClick={() => setTermsOpen(false)}>{t('common.close')}</IonButton>
            </IonButtons>
          </IonToolbar>
        </IonHeader>
        <IonContent className="ion-padding">
          <p>{t('auth.register.termsText')}</p>
        </IonContent>
      </IonModal>
    </PageLayout>
  );
};

export default RegisterPage;
