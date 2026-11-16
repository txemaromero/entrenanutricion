import {
  IonChip,
  IonIcon,
  IonLabel,
  IonNote,
  IonRadio,
  IonRadioGroup,
  IonSelect,
  IonSelectOption,
  IonText,
} from '@ionic/react';
import { checkmarkCircle, ellipseOutline } from 'ionicons/icons';
import { useId } from 'react';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { translateKey } from '../../utils/errors';
import { failedPasswordRules, PASSWORD_RULES } from '../../validation/schemas';

export interface Option {
  value: string | number;
  label: string;
}

interface BaseProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  required?: boolean;
  serverError?: string;
  testId?: string;
}

const FieldError = ({ id, message }: { id: string; message?: string }) =>
  message ? (
    <IonText color="danger" id={id} role="alert">
      <small>{message}</small>
    </IonText>
  ) : null;

export const SelectField = <T extends FieldValues>({
  control,
  name,
  label,
  options,
  required,
  serverError,
  testId,
}: BaseProps<T> & { options: Option[] }) => {
  const { t } = useTranslation();
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const error = translateKey(t, fieldState.error?.message) ?? serverError;
        return (
          <IonSelect
            label={required ? `${label} *` : label}
            labelPlacement="floating"
            fill="outline"
            interface="popover"
            value={field.value}
            onIonChange={(event) => field.onChange(event.detail.value)}
            onIonDismiss={field.onBlur}
            errorText={error}
            className={error ? 'ion-invalid ion-touched' : undefined}
            data-testid={testId ?? `field-${name}`}
          >
            {options.map((option) => (
              <IonSelectOption key={option.value} value={option.value}>
                {option.label}
              </IonSelectOption>
            ))}
          </IonSelect>
        );
      }}
    />
  );
};

/** Single choice as a radio list (accessible, large touch targets). */
export const RadioField = <T extends FieldValues>({
  control,
  name,
  label,
  options,
  required,
  serverError,
  testId,
}: BaseProps<T> & { options: Option[] }) => {
  const { t } = useTranslation();
  const errorId = `error-${useId()}`;
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const error = translateKey(t, fieldState.error?.message) ?? serverError;
        return (
          <fieldset className="choice-fieldset" aria-describedby={error ? errorId : undefined}>
            <legend>{required ? `${label} *` : label}</legend>
            <IonRadioGroup
              value={field.value}
              onIonChange={(event) => field.onChange(event.detail.value)}
              data-testid={testId ?? `field-${name}`}
            >
              {options.map((option) => (
                <IonRadio
                  key={option.value}
                  value={option.value}
                  labelPlacement="end"
                  justify="start"
                  className="choice-radio"
                  data-testid={`option-${name}-${option.value}`}
                >
                  {option.label}
                </IonRadio>
              ))}
            </IonRadioGroup>
            <FieldError id={errorId} message={error} />
          </fieldset>
        );
      }}
    />
  );
};

/**
 * Multi-select as toggle chips. Values in `exclusive` (e.g. "none") clear the rest and are
 * cleared when another option is picked, matching the backend rule.
 */
export const ChipMultiSelect = <T extends FieldValues>({
  control,
  name,
  label,
  options,
  exclusive = [],
  required,
  serverError,
  testId,
}: BaseProps<T> & { options: Option[]; exclusive?: string[] }) => {
  const { t } = useTranslation();
  const errorId = `error-${useId()}`;
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const selected: string[] = field.value ?? [];
        const error = translateKey(t, fieldState.error?.message) ?? serverError;
        const toggle = (value: string) => {
          if (selected.includes(value)) {
            field.onChange(selected.filter((item) => item !== value));
          } else if (exclusive.includes(value)) {
            field.onChange([value]);
          } else {
            field.onChange([...selected.filter((item) => !exclusive.includes(item)), value]);
          }
          field.onBlur();
        };
        return (
          <fieldset
            className="choice-fieldset"
            aria-describedby={error ? errorId : undefined}
            data-testid={testId ?? `field-${name}`}
          >
            <legend>{required ? `${label} *` : label}</legend>
            {/* Keyboard on the group (delegation): an `onKeyDown` on an Ionic component makes its
                React wrapper probe the event with an inline handler, which the CSP blocks. */}
            <div
              className="row row--wrap"
              onKeyDown={(event) => {
                if (event.key !== ' ' && event.key !== 'Enter') return;
                const chip = (event.target as HTMLElement).closest<HTMLElement>('[data-value]');
                if (!chip?.dataset.value) return;
                event.preventDefault();
                toggle(chip.dataset.value);
              }}
            >
              {options.map((option) => {
                const active = selected.includes(String(option.value));
                return (
                  <IonChip
                    key={option.value}
                    color={active ? 'primary' : 'medium'}
                    outline={!active}
                    role="checkbox"
                    aria-checked={active}
                    tabIndex={0}
                    onClick={() => toggle(String(option.value))}
                    data-value={String(option.value)}
                    data-testid={`option-${name}-${option.value}`}
                  >
                    <IonLabel>{option.label}</IonLabel>
                  </IonChip>
                );
              })}
            </div>
            <FieldError id={errorId} message={error} />
          </fieldset>
        );
      }}
    />
  );
};

/** Live checklist of the password policy. */
export const PasswordRequirements = ({ value }: { value: string }) => {
  const { t } = useTranslation();
  const failed = new Set(failedPasswordRules(value ?? ''));
  return (
    <ul className="password-rules" aria-label={t('auth.register.passwordRules')}>
      {PASSWORD_RULES.map((rule) => {
        const ok = !failed.has(rule.code);
        return (
          <li key={rule.code} data-ok={ok} data-testid={`rule-${rule.code}`}>
            <IonIcon
              icon={ok ? checkmarkCircle : ellipseOutline}
              color={ok ? 'success' : 'medium'}
              aria-hidden="true"
            />
            <IonNote color={ok ? 'success' : 'medium'}>
              {t(`auth.register.rules.${rule.code}`)}
              <span className="visually-hidden">
                {ok ? t('auth.register.ruleMet') : t('auth.register.rulePending')}
              </span>
            </IonNote>
          </li>
        );
      })}
    </ul>
  );
};
