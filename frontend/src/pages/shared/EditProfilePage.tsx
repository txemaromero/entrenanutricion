import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonAvatar,
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonIcon,
  IonText,
  useIonRouter,
  useIonToast,
} from '@ionic/react';
import { cameraOutline, personCircleOutline } from 'ionicons/icons';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from '../../validation/zod';

import { meApi } from '../../api/me';
import type { ProfileUpdateInput } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { useAuth } from '../../auth/useAuth';
import { PageLayout } from '../../components/PageLayout';
import { SelectField } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { ChangePasswordModal } from '../../components/profile/ChangePasswordModal';
import { apiFieldError, errorMessage, uploadError } from '../../utils/errors';
import { ACTIVITY_LEVELS, GOALS } from '../../validation/onboarding';
import { nameSchema } from '../../validation/schemas';
import { toNumber } from '../../utils/numbers';

const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

const schema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  currentWeightKg: z
    .number({ error: 'validation.required' })
    .min(30, 'errors.min_value')
    .max(300, 'errors.max_value')
    .optional(),
  goal: z.enum(GOALS).optional(),
  physicalActivityLevel: z.enum(ACTIVITY_LEVELS).optional(),
  weeklyTrainingDays: z.number().int().min(1).max(6).optional(),
});
type ProfileForm = z.infer<typeof schema>;

/** Edit profile (US-10). Saving updates the global user so the profile shows it at once. */
const EditProfilePage = () => {
  const { t } = useTranslation();
  const router = useIonRouter();
  const [toast] = useIonToast();
  const { user, setUser } = useAuth();
  const details = user?.details ?? null;
  const fileInput = useRef<HTMLInputElement>(null);
  const [photo, setPhoto] = useState<File>();
  const [photoError, setPhotoError] = useState<string>();
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [submitError, setSubmitError] = useState<unknown>();
  const preview = useMemo(() => (photo ? URL.createObjectURL(photo) : undefined), [photo]);

  useEffect(() => () => (preview ? URL.revokeObjectURL(preview) : undefined), [preview]);

  const defaults: ProfileForm = {
    firstName: user?.firstName ?? '',
    lastName: user?.lastName ?? '',
    currentWeightKg: details?.currentWeightKg ?? undefined,
    goal: details?.goal,
    physicalActivityLevel: details?.physicalActivityLevel,
    weeklyTrainingDays: details?.weeklyTrainingDays,
  };
  const { control, handleSubmit, formState } = useForm<ProfileForm>({
    resolver: zodResolver(schema),
    defaultValues: defaults,
  });

  const pickPhoto = (file?: File) => {
    setPhotoError(undefined);
    if (!file) return;
    if (!IMAGE_TYPES.includes(file.type)) setPhotoError(t('errors.invalid_file_type'));
    else if (file.size > MAX_IMAGE_BYTES) setPhotoError(t('errors.file_too_large'));
    else setPhoto(file);
  };

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(undefined);
    try {
      if (photo) setUser(await meApi.uploadPhoto(photo, photo.name));
      const changes: ProfileUpdateInput = {
        firstName: values.firstName,
        lastName: values.lastName,
      };
      if (details) {
        if (
          values.currentWeightKg !== undefined &&
          values.currentWeightKg !== details.currentWeightKg
        ) {
          changes.currentWeightKg = values.currentWeightKg;
        }
        changes.goal = values.goal;
        changes.physicalActivityLevel = values.physicalActivityLevel;
        changes.weeklyTrainingDays = values.weeklyTrainingDays;
      }
      setUser(await meApi.updateProfile(changes));
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      if (router.canGoBack()) router.goBack();
      else router.push(PATHS.profile, 'back', 'replace');
    } catch (error) {
      const fileProblem = uploadError(t, error);
      if (fileProblem) setPhotoError(fileProblem);
      else setSubmitError(error);
    }
  });

  if (!user) return null;
  const fieldError = (field: string) => apiFieldError(t, submitError, field);
  const avatar = preview ?? user.profilePhotoUrl;

  return (
    <PageLayout title={t('profile.editTitle')} backHref={PATHS.profile} narrow>
      <form className="stack" onSubmit={onSubmit} noValidate>
        <div className="stack" style={{ alignItems: 'center' }}>
          {avatar ? (
            <IonAvatar className="avatar-lg">
              <img src={avatar} alt={t('profile.photoPreview')} data-testid="photo-preview" />
            </IonAvatar>
          ) : (
            <IonIcon
              icon={personCircleOutline}
              style={{ fontSize: 96 }}
              color="medium"
              aria-hidden="true"
            />
          )}
          <input
            ref={fileInput}
            type="file"
            accept={IMAGE_TYPES.join(',')}
            hidden
            onChange={(event) => pickPhoto(event.target.files?.[0])}
            data-testid="photo-input"
          />
          <IonButton fill="outline" onClick={() => fileInput.current?.click()}>
            <IonIcon slot="start" icon={cameraOutline} aria-hidden="true" />
            {user.profilePhotoUrl || photo ? t('profile.changePhoto') : t('profile.uploadPhoto')}
          </IonButton>
          {photoError && (
            <IonText color="danger" role="alert">
              <small>{photoError}</small>
            </IonText>
          )}
        </div>

        <IonCard>
          <IonCardHeader>
            <IonCardTitle>{t('profile.personalInfo')}</IonCardTitle>
          </IonCardHeader>
          <IonCardContent className="stack">
            <TextField
              control={control}
              name="firstName"
              label={t('auth.register.firstName')}
              required
              serverError={fieldError('firstName')}
            />
            <TextField
              control={control}
              name="lastName"
              label={t('auth.register.lastName')}
              required
              serverError={fieldError('lastName')}
            />
            {details && (
              <TextField
                control={control}
                name="currentWeightKg"
                label={t('profile.currentWeightKg')}
                type="number"
                inputMode="decimal"
                parse={toNumber}
                serverError={fieldError('currentWeightKg')}
              />
            )}
            <IonButton
              fill="clear"
              onClick={() => setPasswordOpen(true)}
              data-testid="open-password-modal"
            >
              {t('profile.changePassword')}
            </IonButton>
          </IonCardContent>
        </IonCard>

        {details && (
          <IonCard>
            <IonCardHeader>
              <IonCardTitle>{t('profile.sportInfo')}</IonCardTitle>
            </IonCardHeader>
            <IonCardContent className="stack">
              <SelectField
                control={control}
                name="goal"
                label={t('profile.goal')}
                options={GOALS.map((value) => ({ value, label: t(`enums.goal.${value}`) }))}
              />
              <SelectField
                control={control}
                name="physicalActivityLevel"
                label={t('profile.activityLevel')}
                options={ACTIVITY_LEVELS.map((value) => ({
                  value,
                  label: t(`enums.activityLevel.${value}`),
                }))}
              />
              <SelectField
                control={control}
                name="weeklyTrainingDays"
                label={t('profile.weeklyDays')}
                options={[1, 2, 3, 4, 5, 6].map((value) => ({
                  value,
                  label: t('onboarding.daysOption', { count: value }),
                }))}
              />
            </IonCardContent>
          </IonCard>
        )}

        {Boolean(submitError) && (
          <IonText color="danger" role="alert">
            <p>{errorMessage(t, submitError)}</p>
          </IonText>
        )}
        <IonButton
          type="submit"
          expand="block"
          disabled={formState.isSubmitting}
          data-testid="profile-save"
        >
          {t('common.saveChanges')}
        </IonButton>
      </form>
      <ChangePasswordModal isOpen={passwordOpen} onClose={() => setPasswordOpen(false)} />
    </PageLayout>
  );
};

export default EditProfilePage;
