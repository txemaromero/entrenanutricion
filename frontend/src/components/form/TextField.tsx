import { IonButton, IonIcon, IonInput } from '@ionic/react';
import { eyeOffOutline, eyeOutline } from 'ionicons/icons';
import { useState, type ComponentProps } from 'react';
import { Controller, type Control, type FieldValues, type Path } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { translateKey } from '../../utils/errors';

type InputProps = ComponentProps<typeof IonInput>;

interface TextFieldProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
  type?: InputProps['type'];
  inputMode?: InputProps['inputmode'];
  autocomplete?: InputProps['autocomplete'];
  placeholder?: string;
  helperText?: string;
  required?: boolean;
  /** Password inputs get a show/hide toggle. */
  revealable?: boolean;
  /** Error coming from the API for this field, already translated. */
  serverError?: string;
  /** Transform the raw text before storing it in the form (e.g. numbers, date masks). */
  parse?: (value: string) => unknown;
  format?: (value: unknown) => string;
  testId?: string;
  onBlurExtra?: (value: unknown) => void;
}

/** IonInput bound to React Hook Form, with translated error text and accessible label. */
export const TextField = <T extends FieldValues>({
  control,
  name,
  label,
  type = 'text',
  inputMode,
  autocomplete,
  placeholder,
  helperText,
  required,
  revealable,
  serverError,
  parse = (value) => value,
  format = (value) => (value === undefined || value === null ? '' : String(value)),
  testId,
  onBlurExtra,
}: TextFieldProps<T>) => {
  const { t } = useTranslation();
  const [revealed, setRevealed] = useState(false);

  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const error = translateKey(t, fieldState.error?.message) ?? serverError;
        return (
          <IonInput
            label={required ? `${label} *` : label}
            labelPlacement="floating"
            fill="outline"
            type={revealable && revealed ? 'text' : type}
            inputmode={inputMode}
            autocomplete={autocomplete}
            placeholder={placeholder}
            value={format(field.value)}
            helperText={helperText}
            errorText={error}
            className={error ? 'ion-invalid ion-touched' : undefined}
            aria-invalid={error ? true : undefined}
            onIonInput={(event) => field.onChange(parse(event.detail.value ?? ''))}
            onIonBlur={() => {
              field.onBlur();
              onBlurExtra?.(field.value);
            }}
            data-testid={testId ?? `field-${name}`}
          >
            {revealable && (
              <IonButton
                slot="end"
                fill="clear"
                className="icon-button"
                aria-label={revealed ? t('auth.login.hidePassword') : t('auth.login.showPassword')}
                onClick={() => setRevealed((value) => !value)}
              >
                <IonIcon
                  slot="icon-only"
                  icon={revealed ? eyeOffOutline : eyeOutline}
                  aria-hidden="true"
                />
              </IonButton>
            )}
          </IonInput>
        );
      }}
    />
  );
};
