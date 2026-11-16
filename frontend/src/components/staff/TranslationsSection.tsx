import { IonLabel, IonSegment, IonSegmentButton, IonText } from '@ionic/react';
import { useState } from 'react';
import { useFormState, useWatch, type Control, type FieldValues, type Path } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import type { TranslatedTextKey } from '../../api/types';
import { TRANSLATION_LANGUAGES, type TranslationLanguage } from '../../utils/translations';
import { TextField } from '../form/TextField';
import { FormSection } from './FormShell';

const preview = (text: unknown) => {
  const value = typeof text === 'string' ? text.trim() : '';
  return value.length > 80 ? `${value.slice(0, 80)}…` : value;
};

/**
 * English and Catalan texts of a catalog item. The Spanish fields of the form are the base text:
 * a translation left empty is shown in Spanish. The Spanish text is shown under each field.
 */
export const TranslationsSection = <T extends FieldValues>({
  control,
  fields,
  stepsField,
}: {
  control: Control<T>;
  fields: { key: TranslatedTextKey; label: string }[];
  /** Exercises: the field array of the steps (`[{ text }]`), translated one by one. */
  stepsField?: Path<T>;
}) => {
  const { t } = useTranslation();
  const [language, setLanguage] = useState<TranslationLanguage>('en');
  const base = useWatch({ control, name: fields.map((field) => field.key) as Path<T>[] });
  const steps = (useWatch({ control, name: (stepsField ?? fields[0].key) as Path<T> }) ??
    []) as unknown;
  const baseSteps = stepsField && Array.isArray(steps) ? (steps as { text?: string }[]) : [];
  const { errors } = useFormState({ control, name: 'translations' as Path<T> });
  const translationErrors = (errors as { translations?: Record<string, unknown> }).translations;
  const withErrors = TRANSLATION_LANGUAGES.filter(
    (code) => code !== language && translationErrors?.[code],
  );

  return (
    <FormSection title={t('translations.title')}>
      <p className="muted" style={{ margin: 0 }}>
        {t('translations.intro')}
      </p>
      <IonSegment
        value={language}
        onIonChange={(event) => setLanguage(event.detail.value as TranslationLanguage)}
        aria-label={t('translations.title')}
        data-testid="translations-language"
      >
        {TRANSLATION_LANGUAGES.map((code) => (
          <IonSegmentButton key={code} value={code} data-testid={`translations-${code}`}>
            <IonLabel>{t(`language.${code}`)}</IonLabel>
          </IonSegmentButton>
        ))}
      </IonSegment>
      {withErrors.length > 0 && (
        <IonText color="danger" role="alert" data-testid="translations-errors">
          <small>
            {t('translations.errorsIn', {
              languages: withErrors.map((code) => t(`language.${code}`)).join(', '),
            })}
          </small>
        </IonText>
      )}
      {fields.map((field, index) => (
        <TextField
          key={`${language}.${field.key}`}
          control={control}
          name={`translations.${language}.${field.key}` as Path<T>}
          label={field.label}
          helperText={
            preview(base[index]) ? t('translations.original', { text: preview(base[index]) }) : ''
          }
          testId={`translation-${language}-${field.key}`}
        />
      ))}
      {baseSteps.map((step, index) => (
        <TextField
          key={`${language}.steps.${index}`}
          control={control}
          name={`translations.${language}.steps.${index}` as Path<T>}
          label={t('translations.step', { number: index + 1 })}
          helperText={
            preview(step.text) ? t('translations.original', { text: preview(step.text) }) : ''
          }
          testId={`translation-${language}-step-${index}`}
        />
      ))}
    </FormSection>
  );
};
