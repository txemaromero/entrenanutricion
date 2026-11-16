import { z } from './zod';

/**
 * Validation shared with the backend. Error messages are i18n keys,
 * translated by the form components: `errors.*` (same codes as the API) or `validation.*`.
 */

// Letters of any script separated by single spaces, hyphens or apostrophes
// (mirrors PERSON_NAME_RE in backend/apps/core/validators.py).
export const NAME_PATTERN = /^\p{L}+(?:[ '’-]\p{L}+)*$/u;

export const MIN_AGE = 18;
export const MAX_AGE = 120;

export const PASSWORD_RULES = [
  { code: 'password_too_short', test: (value: string) => value.length >= 8 },
  { code: 'password_no_upper', test: (value: string) => /\p{Lu}/u.test(value) },
  { code: 'password_no_lower', test: (value: string) => /\p{Ll}/u.test(value) },
  { code: 'password_no_digit', test: (value: string) => /[0-9]/.test(value) },
  { code: 'password_no_symbol', test: (value: string) => /[^\p{L}\p{N}\s]/u.test(value) },
] as const;

export const failedPasswordRules = (value: string): string[] =>
  PASSWORD_RULES.filter((rule) => !rule.test(value)).map((rule) => rule.code);

export const nameSchema = z
  .string()
  .trim()
  .min(1, 'validation.required')
  .max(150, 'errors.max_length')
  .regex(NAME_PATTERN, 'errors.invalid_name');

export const emailSchema = z
  .string()
  .trim()
  .min(1, 'validation.required')
  .pipe(z.email('validation.email'));

/** Same limit as the API. */
export const MAX_PASSWORD_LENGTH = 128;

export const passwordSchema = z
  .string()
  .max(MAX_PASSWORD_LENGTH, 'errors.max_length')
  .superRefine((value, context) => {
    const failed = failedPasswordRules(value);
    if (failed.length) context.addIssue({ code: 'custom', message: `errors.${failed[0]}` });
  });

export const ageOn = (birthDate: Date, today: Date): number => {
  const beforeBirthday =
    today.getMonth() < birthDate.getMonth() ||
    (today.getMonth() === birthDate.getMonth() && today.getDate() < birthDate.getDate());
  return today.getFullYear() - birthDate.getFullYear() - (beforeBirthday ? 1 : 0);
};

/** "dd/mm/aaaa" → "aaaa-mm-dd", or null when it is not a real calendar date. */
export const displayDateToIso = (value: string): string | null => {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(value.trim());
  if (!match) return null;
  const [, day, month, year] = match.map(Number);
  const date = new Date(year, month - 1, day);
  if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) {
    return null;
  }
  return `${match[3]}-${match[2]}-${match[1]}`;
};

export const birthDateSchema = (today: () => Date = () => new Date()) =>
  z
    .string()
    .min(1, 'validation.required')
    .superRefine((value, context) => {
      const iso = displayDateToIso(value);
      if (!iso) {
        context.addIssue({ code: 'custom', message: 'validation.dateFormat' });
        return;
      }
      const [year, month, day] = iso.split('-').map(Number);
      const age = ageOn(new Date(year, month - 1, day), today());
      if (age < MIN_AGE) context.addIssue({ code: 'custom', message: 'errors.too_young' });
      else if (age > MAX_AGE) context.addIssue({ code: 'custom', message: 'errors.too_old' });
    });

/** Keep only digits and insert the slashes of dd/mm/aaaa while typing. */
export const maskDisplayDate = (value: string): string => {
  const digits = value.replace(/\D/g, '').slice(0, 8);
  return [digits.slice(0, 2), digits.slice(2, 4), digits.slice(4)].filter(Boolean).join('/');
};

export const registerSchema = (today?: () => Date) =>
  z.object({
    firstName: nameSchema,
    lastName: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    birthDate: birthDateSchema(today),
    gender: z.enum(['M', 'F', 'O'], { error: 'validation.required' }),
    termsAccepted: z.boolean().refine((value) => value, { message: 'errors.terms_required' }),
    healthDataConsent: z
      .boolean()
      .refine((value) => value, { message: 'errors.health_consent_required' }),
  });

export type RegisterForm = z.input<ReturnType<typeof registerSchema>>;

export const passwordChangeSchema = z
  .object({
    currentPassword: z.string().min(1, 'validation.required'),
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, 'validation.required'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'errors.passwords_do_not_match',
  });

export type PasswordChangeForm = z.infer<typeof passwordChangeSchema>;

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, 'validation.required').max(MAX_PASSWORD_LENGTH, 'errors.max_length'),
  rememberMe: z.boolean(),
});

export type LoginForm = z.infer<typeof loginSchema>;

export const forgotPasswordSchema = z.object({ email: emailSchema });

export type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z
  .object({
    newPassword: passwordSchema,
    confirmPassword: z.string().min(1, 'validation.required'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    path: ['confirmPassword'],
    message: 'errors.passwords_do_not_match',
  });

export type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;
