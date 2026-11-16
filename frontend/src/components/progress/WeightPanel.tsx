import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonCard, IonCardContent, IonText, useIonToast } from '@ionic/react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { z } from '../../validation/zod';

import { progressApi } from '../../api/client-features';
import type { WeightSummary } from '../../api/types';
import { formatDate, formatNumber, toIsoDate } from '../../i18n/format';
import { apiFieldError, errorMessage } from '../../utils/errors';
import { toNumber } from '../../utils/numbers';
import { newBadgesText } from '../../utils/badges';
import { WeightChart } from '../charts';
import { TextField } from '../form/TextField';

const schema = z.object({
  weightKg: z
    .number({ error: 'validation.required' })
    .min(30, 'errors.min_value')
    .max(300, 'errors.max_value'),
  date: z
    .string()
    .min(1, 'validation.required')
    .refine((value) => value <= toIsoDate(new Date()), 'errors.future_date'),
});
type WeightForm = z.infer<typeof schema>;

/** Add-weight form + evolution chart. The chart redraws from the POST response at once. */
export const WeightPanel = ({
  summary,
  onChange,
}: {
  summary: WeightSummary;
  onChange: (summary: WeightSummary) => void;
}) => {
  const { t, i18n } = useTranslation();
  const [toast] = useIonToast();
  const [submitError, setSubmitError] = useState<unknown>();
  const { control, handleSubmit, reset, formState } = useForm<WeightForm>({
    resolver: zodResolver(schema),
    defaultValues: { weightKg: undefined, date: toIsoDate(new Date()) },
  });

  const onSubmit = handleSubmit(async ({ weightKg, date }) => {
    setSubmitError(undefined);
    try {
      const updated = await progressApi.addWeight(weightKg, date);
      onChange(updated);
      reset({ weightKg: undefined, date: toIsoDate(new Date()) });
      const badges = newBadgesText(t, updated.newBadges);
      void toast({
        message: badges ? `${t('progress.weightSaved')}. ${badges}` : t('progress.weightSaved'),
        duration: badges ? 4000 : 2000,
        color: 'success',
      });
    } catch (error) {
      setSubmitError(error);
    }
  });

  const recent = [...summary.records].reverse().slice(0, 5);

  return (
    <div className="stack">
      <IonCard>
        <IonCardContent>
          <form className="stack" onSubmit={onSubmit} noValidate>
            <TextField
              control={control}
              name="weightKg"
              label={t('progress.weightKg')}
              type="number"
              inputMode="decimal"
              required
              parse={toNumber}
              serverError={apiFieldError(t, submitError, 'weightKg')}
            />
            <TextField
              control={control}
              name="date"
              label={t('progress.date')}
              type="date"
              required
              serverError={apiFieldError(t, submitError, 'date')}
            />
            {Boolean(submitError) && !apiFieldError(t, submitError, 'weightKg') && (
              <IonText color="danger" role="alert">
                <small>{errorMessage(t, submitError)}</small>
              </IonText>
            )}
            <IonButton type="submit" disabled={formState.isSubmitting} data-testid="add-weight">
              {t('progress.addWeight')}
            </IonButton>
          </form>
        </IonCardContent>
      </IonCard>

      <IonCard>
        <IonCardContent>
          <WeightChart summary={summary} />
          <p className="muted">
            {t('progress.weightSummary', {
              initial: formatNumber(summary.initialWeightKg, i18n.language),
              current: formatNumber(
                summary.currentWeightKg ?? summary.initialWeightKg,
                i18n.language,
              ),
              target: formatNumber(summary.targetWeightKg, i18n.language),
            })}
          </p>
        </IonCardContent>
      </IonCard>

      <ul className="stack" style={{ listStyle: 'none', padding: 0 }} data-testid="weight-list">
        {recent.map((record) => (
          <li key={record.id} className="row row--between">
            <span>{formatDate(record.date, i18n.language)}</span>
            <strong>
              {formatNumber(record.weightKg, i18n.language)} {t('common.kg')}
            </strong>
          </li>
        ))}
      </ul>
    </div>
  );
};
