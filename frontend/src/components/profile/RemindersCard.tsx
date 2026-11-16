import { zodResolver } from '@hookform/resolvers/zod';
import {
  IonButton,
  IonCard,
  IonCardContent,
  IonCardHeader,
  IonCardTitle,
  IonText,
  IonToggle,
  useIonToast,
} from '@ionic/react';
import { useEffect, useRef } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { remindersApi } from '../../api/client-features';
import type { Reminders } from '../../api/types';
import { useAuth } from '../../auth/useAuth';
import { useResource } from '../../hooks/useResource';
import { errorMessage } from '../../utils/errors';
import { remindersSchema, type RemindersForm } from '../../validation/training';
import { TextField } from '../form/TextField';

const toForm = (reminders: Reminders): RemindersForm => ({
  enabled: reminders.enabled,
  trainingTime: reminders.trainingTime,
});

/** Profile (client): the time they train at (countdown) and email reminders on training days. */
export const RemindersCard = () => {
  const { t } = useTranslation();
  const [toast] = useIonToast();
  const { user } = useAuth();
  const { data, setData } = useResource(remindersApi.get);
  const { control, handleSubmit, reset, getValues, formState } = useForm<RemindersForm>({
    resolver: zodResolver(remindersSchema),
    defaultValues: { enabled: false, trainingTime: '18:00' },
  });
  // Fill the form once: reloads on entering the view must not undo what is being edited.
  const filled = useRef(false);
  useEffect(() => {
    if (data && !filled.current) {
      filled.current = true;
      reset(toForm(data));
    }
  }, [data, reset]);

  const save = async (enabled: boolean, trainingTime: string | null) => {
    try {
      const updated = await remindersApi.update(enabled, trainingTime);
      setData(updated);
      reset(toForm(updated));
      void toast({ message: t('reminders.saved'), duration: 2000, color: 'success' });
    } catch (error) {
      void toast({ message: errorMessage(t, error), duration: 3000, color: 'danger' });
    }
  };

  const onSubmit = handleSubmit(({ enabled, trainingTime }) => save(enabled, trainingTime));

  if (!data) return null;

  return (
    <IonCard data-testid="reminders-card">
      <IonCardHeader>
        <IonCardTitle>{t('reminders.title')}</IonCardTitle>
      </IonCardHeader>
      <IonCardContent>
        <form className="stack" onSubmit={onSubmit} noValidate>
          <Controller
            control={control}
            name="enabled"
            render={({ field }) => (
              <IonToggle
                checked={field.value}
                justify="space-between"
                onIonChange={(event) => field.onChange(event.detail.checked)}
                data-testid="reminders-enabled"
              >
                {t('reminders.enabled')}
              </IonToggle>
            )}
          />
          <TextField
            control={control}
            name="trainingTime"
            label={t('reminders.trainingTime')}
            type="time"
            helperText={
              data.customTime
                ? undefined
                : t('reminders.defaultTime', { time: data.defaultTrainingTime })
            }
            testId="reminders-time"
          />
          <small className="muted">{t('reminders.help')}</small>
          {user && !user.emailVerified && (
            <IonText color="warning" data-testid="reminders-need-verification">
              <small>{t('reminders.needsVerification')}</small>
            </IonText>
          )}
          <div className="row row--wrap">
            <IonButton type="submit" disabled={formState.isSubmitting} data-testid="save-reminders">
              {t('common.save')}
            </IonButton>
            {data.customTime && (
              <IonButton
                fill="clear"
                onClick={() => void save(getValues('enabled'), null)}
                data-testid="reset-training-time"
              >
                {t('reminders.useDefault', { time: data.defaultTrainingTime })}
              </IonButton>
            )}
          </div>
        </form>
      </IonCardContent>
    </IonCard>
  );
};
