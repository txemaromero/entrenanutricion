import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonIcon, IonText, useIonRouter, useIonToast } from '@ionic/react';
import { cameraOutline } from 'ionicons/icons';
import { useMemo, useRef, useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';

import { usersApi } from '../../api/staff';
import type { UserDetail, UserUpdateInput } from '../../api/types';
import { PATHS } from '../../auth/routing';
import { PageLayout } from '../../components/PageLayout';
import { ErrorState, ListSkeleton } from '../../components/States';
import { PasswordRequirements, SelectField } from '../../components/form/fields';
import { TextField } from '../../components/form/TextField';
import { FormActions, FormSection } from '../../components/staff/FormShell';
import { useFormInit } from '../../hooks/useFormInit';
import { useLeaveForm } from '../../hooks/useLeaveForm';
import { useResource } from '../../hooks/useResource';
import { applyServerErrors, uploadError } from '../../utils/errors';
import { toNumber } from '../../utils/numbers';
import { ACTIVITY_LEVELS, GOALS } from '../../validation/onboarding';
import { displayDateToIso, maskDisplayDate } from '../../validation/schemas';
import {
  ROLES,
  userCreateSchema,
  userEditSchema,
  type UserCreateForm,
  type UserEditForm,
} from '../../validation/staff';

const roleOptions = (t: (key: string) => string) =>
  ROLES.map((value) => ({ value, label: t(`enums.role.${value}`) }));

/** Admin: create a user of any role (US-21). Every field is required. */
export const UserCreatePage = () => {
  const { t } = useTranslation();
  const router = useIonRouter();
  const [toast] = useIonToast();
  const [saveError, setSaveError] = useState<unknown>();
  const schema = useMemo(() => userCreateSchema(), []);
  const { control, handleSubmit, setError, formState } = useForm<UserCreateForm>({
    resolver: zodResolver(schema),
    defaultValues: { firstName: '', lastName: '', email: '', password: '', birthDate: '' },
  });
  const password = useWatch({ control, name: 'password' });

  const onSubmit = handleSubmit(async (values) => {
    setSaveError(undefined);
    try {
      const created = await usersApi.create({
        ...values,
        email: values.email.trim(),
        birthDate: displayDateToIso(values.birthDate)!,
      });
      void toast({ message: t('users.created'), duration: 2000, color: 'success' });
      router.push(`${PATHS.users}/${created.id}`, 'forward', 'replace');
    } catch (error) {
      if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  return (
    <PageLayout title={t('users.new')} backHref={PATHS.users} narrow>
      <form className="stack" onSubmit={onSubmit} noValidate>
        <TextField
          control={control}
          name="firstName"
          label={t('auth.register.firstName')}
          required
        />
        <TextField control={control} name="lastName" label={t('auth.register.lastName')} required />
        <TextField
          control={control}
          name="email"
          label={t('auth.login.email')}
          type="email"
          inputMode="email"
          required
        />
        <TextField
          control={control}
          name="password"
          label={t('auth.login.password')}
          type="password"
          revealable
          required
        />
        <PasswordRequirements value={password} />
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
        <SelectField
          control={control}
          name="role"
          label={t('users.role')}
          required
          options={roleOptions(t)}
        />
        <TextField
          control={control}
          name="birthDate"
          label={t('auth.register.birthDate')}
          placeholder={t('auth.register.datePlaceholder')}
          inputMode="numeric"
          required
          parse={(value) => maskDisplayDate(String(value))}
        />
        <FormActions
          onCancel={() => router.goBack()}
          saving={formState.isSubmitting}
          error={saveError}
        />
      </form>
    </PageLayout>
  );
};

const toEditForm = (user: UserDetail): UserEditForm => ({
  firstName: user.firstName,
  lastName: user.lastName,
  role: user.role,
  currentWeightKg: user.details?.currentWeightKg ?? undefined,
  goal: user.details?.goal,
  physicalActivityLevel: user.details?.physicalActivityLevel,
  weeklyTrainingDays: user.details?.weeklyTrainingDays,
});

/** Admin: edit names, current weight, goals, role and photo (US-22, regression #2). */
export const UserEditPage = () => {
  const { t } = useTranslation();
  const id = Number(useParams<{ id: string }>().id);
  const router = useIonRouter();
  const leave = useLeaveForm(`${PATHS.users}/${id}`);
  const [toast] = useIonToast();
  const fileInput = useRef<HTMLInputElement>(null);
  const [photo, setPhoto] = useState<File>();
  const [photoError, setPhotoError] = useState<string>();
  const [saveError, setSaveError] = useState<unknown>();
  const existing = useResource(() => usersApi.get(id), [id]);
  const { control, handleSubmit, reset, setError, formState } = useForm<UserEditForm>({
    resolver: zodResolver(userEditSchema),
  });

  useFormInit(existing.data, reset, toEditForm);

  const details = existing.data?.details;

  const onSubmit = handleSubmit(async (values) => {
    setSaveError(undefined);
    try {
      const changes: UserUpdateInput = {
        firstName: values.firstName,
        lastName: values.lastName,
        role: values.role,
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
      await usersApi.update(id, changes);
      if (photo) await usersApi.uploadPhoto(id, photo, photo.name);
      void toast({ message: t('common.saved'), duration: 2000, color: 'success' });
      leave();
    } catch (error) {
      const fileProblem = uploadError(t, error);
      if (fileProblem) setPhotoError(fileProblem);
      else if (!applyServerErrors(error, setError)) setSaveError(error);
    }
  });

  const pickPhoto = (file?: File) => {
    if (!file) return;
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
      setPhotoError(t('errors.invalid_file_type'));
    } else if (file.size > 5 * 1024 * 1024) {
      setPhotoError(t('errors.file_too_large'));
    } else {
      setPhotoError(undefined);
      setPhoto(file);
    }
  };

  return (
    <PageLayout title={t('users.edit')} backHref={`${PATHS.users}/${id}`} narrow>
      {existing.loading && !existing.data && <ListSkeleton />}
      {existing.error && <ErrorState error={existing.error} onRetry={existing.reload} />}
      {existing.data && (
        <form className="stack" onSubmit={onSubmit} noValidate>
          <FormSection title={t('profile.personalInfo')}>
            <TextField
              control={control}
              name="firstName"
              label={t('auth.register.firstName')}
              required
            />
            <TextField
              control={control}
              name="lastName"
              label={t('auth.register.lastName')}
              required
            />
            {details && (
              <TextField
                control={control}
                name="currentWeightKg"
                label={t('profile.currentWeightKg')}
                type="number"
                inputMode="decimal"
                parse={toNumber}
              />
            )}
            <SelectField
              control={control}
              name="role"
              label={t('users.role')}
              required
              options={roleOptions(t)}
            />
            <input
              ref={fileInput}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              hidden
              onChange={(event) => pickPhoto(event.target.files?.[0])}
              data-testid="photo-input"
            />
            <IonButton fill="outline" onClick={() => fileInput.current?.click()}>
              <IonIcon slot="start" icon={cameraOutline} aria-hidden="true" />
              {photo ? photo.name : t('profile.changePhoto')}
            </IonButton>
            {photoError && (
              <IonText color="danger" role="alert">
                <small>{photoError}</small>
              </IonText>
            )}
          </FormSection>
          {details && (
            <FormSection title={t('profile.sportInfo')}>
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
            </FormSection>
          )}
          <FormActions
            onCancel={() => router.goBack()}
            saving={formState.isSubmitting}
            error={saveError}
          />
        </form>
      )}
    </PageLayout>
  );
};
