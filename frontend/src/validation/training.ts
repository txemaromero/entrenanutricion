import { z } from './zod';

/** Same limits as the backend (`SetEntrySerializer`, `MAX_SETS`). */
export const MAX_SETS = 20;

const oneDecimal = (value: number) => Math.abs(value * 10 - Math.round(value * 10)) < 1e-9;

export const setsSchema = z.object({
  sets: z
    .array(
      z.object({
        reps: z
          .number({ error: 'validation.required' })
          .int('errors.invalid')
          .min(0, 'errors.min_value')
          .max(200, 'errors.max_value'),
        weightKg: z
          .number()
          .min(0, 'errors.min_value')
          .max(500, 'errors.max_value')
          .refine(oneDecimal, 'errors.max_decimal_places')
          .optional(),
      }),
    )
    .min(1, 'sets.atLeastOne')
    .max(MAX_SETS, 'errors.max_value'),
});
export type SetsForm = z.infer<typeof setsSchema>;

export const remindersSchema = z.object({
  enabled: z.boolean(),
  trainingTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/, 'errors.invalid'),
});
export type RemindersForm = z.infer<typeof remindersSchema>;
