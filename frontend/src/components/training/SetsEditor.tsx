import { zodResolver } from '@hookform/resolvers/zod';
import { IonButton, IonIcon, IonText } from '@ionic/react';
import { add, barbellOutline, trashOutline } from 'ionicons/icons';
import { useState } from 'react';
import { useFieldArray, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import type { DayExercise, SetEntry } from '../../api/types';
import { toNumber } from '../../utils/numbers';
import { formatSets, initialSets } from '../../utils/sets';
import { translateKey } from '../../utils/errors';
import { MAX_SETS, setsSchema, type SetsForm } from '../../validation/training';
import { TextField } from '../form/TextField';

const toForm = (item: DayExercise): SetsForm => ({
  sets: initialSets(item.sets, item.reps, item.loggedSets, item.lastSets).map((entry) => ({
    reps: entry.reps,
    weightKg: entry.weightKg ?? undefined,
  })),
});

/**
 * Sets actually done for one exercise: reps and kg per set, prefilled with the plan and the load
 * of the last session. Saving also marks the exercise as done.
 */
export const SetsEditor = ({
  item,
  readOnly,
  onSave,
}: {
  item: DayExercise;
  readOnly: boolean;
  /** Resolves to true when the sets were saved (or queued without coverage). */
  onSave: (sets: SetEntry[]) => Promise<boolean>;
}) => {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const { control, handleSubmit, reset, getValues, formState } = useForm<SetsForm>({
    resolver: zodResolver(setsSchema),
    defaultValues: toForm(item),
  });
  const rows = useFieldArray({ control, name: 'sets' });
  const testId = (name: string) => `${name}-${item.order}`;

  const toggle = () => {
    if (!open) reset(toForm(item));
    setOpen((value) => !value);
  };

  const onSubmit = handleSubmit(async ({ sets }) => {
    const saved = await onSave(
      sets.map((entry) => ({ reps: entry.reps, weightKg: entry.weightKg ?? null })),
    );
    if (saved) setOpen(false);
  });

  const listError = translateKey(t, formState.errors.sets?.root?.message);
  const logged = item.loggedSets.length > 0;

  return (
    <div className="stack" style={{ gap: 8 }}>
      {logged && (
        <p className="muted" style={{ margin: 0 }} data-testid={testId('logged-sets')}>
          {t('sets.logged', { sets: formatSets(t, item.loggedSets, i18n.language) })}
        </p>
      )}
      {!readOnly && (
        <IonButton
          fill="clear"
          size="small"
          className="ion-no-margin"
          style={{ alignSelf: 'flex-start' }}
          onClick={toggle}
          aria-expanded={open}
          data-testid={testId('sets-toggle')}
        >
          <IonIcon slot="start" icon={barbellOutline} aria-hidden="true" />
          {logged ? t('sets.edit') : t('sets.log')}
        </IonButton>
      )}
      {open && !readOnly && (
        <form className="stack" onSubmit={onSubmit} noValidate data-testid={testId('sets-form')}>
          {item.lastSets && (
            <p className="muted" style={{ margin: 0 }} data-testid={testId('last-sets')}>
              {t('sets.lastTime', { sets: formatSets(t, item.lastSets, i18n.language) })}
            </p>
          )}
          {rows.fields.map((field, index) => (
            <div key={field.id} className="sets-row" data-testid={`set-row-${item.order}-${index}`}>
              <strong>{t('sets.number', { number: index + 1 })}</strong>
              <TextField
                control={control}
                name={`sets.${index}.reps`}
                label={t('sets.reps')}
                type="number"
                inputMode="numeric"
                parse={toNumber}
                testId={`set-reps-${item.order}-${index}`}
              />
              <TextField
                control={control}
                name={`sets.${index}.weightKg`}
                label={t('sets.weight')}
                type="number"
                inputMode="decimal"
                parse={toNumber}
                testId={`set-weight-${item.order}-${index}`}
              />
              <IonButton
                fill="clear"
                color="danger"
                className="icon-button"
                disabled={rows.fields.length === 1}
                onClick={() => rows.remove(index)}
                aria-label={t('sets.remove', { number: index + 1 })}
                data-testid={`remove-set-${item.order}-${index}`}
              >
                <IonIcon slot="icon-only" icon={trashOutline} aria-hidden="true" />
              </IonButton>
            </div>
          ))}
          <small className="muted">{t('sets.noLoadHint')}</small>
          {listError && (
            <IonText color="danger" role="alert">
              <small>{listError}</small>
            </IonText>
          )}
          <div className="row row--wrap">
            <IonButton
              fill="outline"
              size="small"
              disabled={rows.fields.length >= MAX_SETS}
              onClick={() => {
                const last = getValues('sets').at(-1);
                rows.append({ reps: last?.reps ?? item.reps, weightKg: last?.weightKg });
              }}
              data-testid={testId('add-set')}
            >
              <IonIcon slot="start" icon={add} aria-hidden="true" />
              {t('sets.add')}
            </IonButton>
            <IonButton
              type="submit"
              size="small"
              disabled={formState.isSubmitting}
              data-testid={testId('save-sets')}
            >
              {t('sets.save')}
            </IonButton>
          </div>
        </form>
      )}
    </div>
  );
};
