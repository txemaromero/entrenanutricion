import { z } from './zod';

import { FOOD_CATEGORIES, OPTIONAL_NUTRIENTS, type NutrientKey } from '../utils/foods';
import { MEAL_KEYS } from '../utils/nutrition';
import { ACTIVITY_LEVELS, EQUIPMENT, GOALS } from './onboarding';
import { birthDateSchema, emailSchema, nameSchema, passwordSchema } from './schemas';

/** Management forms. Same limits as the backend. */

const requiredNumber = (min: number, max: number, int = true) => {
  const base = z.number({ error: 'validation.required' });
  return (int ? base.int('errors.invalid') : base)
    .min(min, 'errors.min_value')
    .max(max, 'errors.max_value');
};

const title = z.string().trim().min(1, 'validation.required').max(120, 'errors.max_length');

/** English and Catalan texts (optional; empty means "show the Spanish one"). */
const translatedTexts = z.object({
  name: z.string().trim().max(120, 'errors.max_length').optional(),
  description: z.string().max(5000, 'errors.max_length').optional(),
  technique: z.string().max(5000, 'errors.max_length').optional(),
  commonMistakes: z.string().max(5000, 'errors.max_length').optional(),
  benefits: z.string().max(5000, 'errors.max_length').optional(),
  // A step left untranslated arrives empty (it is shown in Spanish).
  steps: z.array(z.string().max(1000, 'errors.max_length').optional()).optional(),
});
export const translationsSchema = z.object({ en: translatedTexts, ca: translatedTexts });

export const workoutSchema = z.object({
  translations: translationsSchema.optional(),
  name: title,
  description: z.string(),
  durationMinutes: requiredNumber(1, 600).optional(),
  exercises: z
    .array(
      z.object({
        id: z.number().optional(),
        exerciseId: z
          .number()
          .optional()
          .refine((value) => value !== undefined, 'validation.required'),
        sets: requiredNumber(1, 20),
        reps: requiredNumber(1, 100),
        restSeconds: requiredNumber(0, 600),
      }),
    )
    .min(1, 'errors.exercises_required'),
});
export type WorkoutForm = z.infer<typeof workoutSchema>;

export const exerciseSchema = z.object({
  translations: translationsSchema.optional(),
  name: title,
  description: z.string(),
  technique: z.string(),
  commonMistakes: z.string(),
  benefits: z.string(),
  muscleGroupIds: z.array(z.string()),
  steps: z.array(z.object({ text: z.string().trim().min(1, 'validation.required') })),
});
export type ExerciseForm = z.infer<typeof exerciseSchema>;

export const DIFFICULTIES = ['beginner', 'intermediate', 'advanced'] as const;

export const planSchema = z.object({
  translations: translationsSchema.optional(),
  name: title,
  description: z.string(),
  goal: z.enum(GOALS, { error: 'validation.required' }),
  difficulty: z.enum(DIFFICULTIES, { error: 'validation.required' }),
  equipment: z.enum(EQUIPMENT, { error: 'validation.required' }),
  durationWeeks: requiredNumber(1, 52),
  workouts: z
    .array(z.object({ id: z.number().optional(), workoutId: z.number() }))
    .min(1, 'errors.workouts_required'),
});
export type PlanForm = z.infer<typeof planSchema>;

export const CATEGORIES = ['weight_loss', 'muscle_gain', 'maintenance'] as const;
export const DIET_LABELS = [
  'balanced',
  'high_protein',
  'low_carb',
  'low_fat',
  'mediterranean',
  'vegetarian',
  'vegan',
  'keto',
] as const;

const macro = z
  .number({ error: 'validation.required' })
  .gt(0, 'errors.min_value')
  .max(99999, 'errors.max_value');

export const mealPlanSchema = z
  .object({
    translations: translationsSchema.optional(),
    name: title,
    category: z.enum(CATEGORIES, { error: 'validation.required' }),
    dietLabel: z.enum(DIET_LABELS, { error: 'validation.required' }),
    calories: requiredNumber(1, 20000),
    proteinsG: macro,
    carbsG: macro,
    fatsG: macro,
    description: z.string(),
    mealDistribution: z.object(
      Object.fromEntries(MEAL_KEYS.map((key) => [key, requiredNumber(0, 100)])) as Record<
        (typeof MEAL_KEYS)[number],
        ReturnType<typeof requiredNumber>
      >,
    ),
  })
  .superRefine((data, context) => {
    const sum = MEAL_KEYS.reduce((total, key) => total + (data.mealDistribution[key] ?? 0), 0);
    if (sum !== 100) {
      context.addIssue({
        code: 'custom',
        path: ['mealDistribution'],
        message: 'errors.distribution_sum',
      });
    }
  });
export type MealPlanForm = z.infer<typeof mealPlanSchema>;

const gramsPer100 = z
  .number({ error: 'validation.required' })
  .min(0, 'errors.min_value')
  .max(100, 'errors.max_value');
const optionalAmount = (max: number) =>
  z.number().min(0, 'errors.min_value').max(max, 'errors.max_value').nullable().optional();
const GRAM_NUTRIENTS: NutrientKey[] = ['fiberG', 'sugarsG', 'saturatedFatG'];

/** Food per 100 g; same rules as the backend (macros ≤ 100 g, sugars ≤ carbs, saturated ≤ fats). */
export const foodSchema = z
  .object({
    translations: translationsSchema.optional(),
    name: title,
    category: z.enum(FOOD_CATEGORIES, { error: 'validation.required' }),
    calories: requiredNumber(0, 900, false),
    proteinsG: gramsPer100,
    carbsG: gramsPer100,
    fatsG: gramsPer100,
    ...(Object.fromEntries(
      OPTIONAL_NUTRIENTS.map((key) => [
        key,
        optionalAmount(GRAM_NUTRIENTS.includes(key) ? 100 : 99999),
      ]),
    ) as Record<NutrientKey, ReturnType<typeof optionalAmount>>),
  })
  .superRefine((data, context) => {
    if ((data.proteinsG ?? 0) + (data.carbsG ?? 0) + (data.fatsG ?? 0) > 100) {
      context.addIssue({ code: 'custom', path: ['fatsG'], message: 'errors.macros_exceed_100g' });
    }
    if (data.sugarsG != null && data.sugarsG > data.carbsG) {
      context.addIssue({
        code: 'custom',
        path: ['sugarsG'],
        message: 'errors.sugars_exceed_carbs',
      });
    }
    if (data.saturatedFatG != null && data.saturatedFatG > data.fatsG) {
      context.addIssue({
        code: 'custom',
        path: ['saturatedFatG'],
        message: 'errors.saturated_exceed_fats',
      });
    }
  });
export type FoodForm = z.infer<typeof foodSchema>;

export const ROLES = ['client', 'trainer', 'nutritionist', 'admin'] as const;

export const userCreateSchema = (today?: () => Date) =>
  z.object({
    firstName: nameSchema,
    lastName: nameSchema,
    email: emailSchema,
    password: passwordSchema,
    gender: z.enum(['M', 'F', 'O'], { error: 'validation.required' }),
    role: z.enum(ROLES, { error: 'validation.required' }),
    birthDate: birthDateSchema(today),
  });
export type UserCreateForm = z.input<ReturnType<typeof userCreateSchema>>;

export const userEditSchema = z.object({
  firstName: nameSchema,
  lastName: nameSchema,
  role: z.enum(ROLES),
  currentWeightKg: z.number().min(30, 'errors.min_value').max(300, 'errors.max_value').optional(),
  goal: z.enum(GOALS).optional(),
  physicalActivityLevel: z.enum(ACTIVITY_LEVELS).optional(),
  weeklyTrainingDays: z.number().int().min(1).max(6).optional(),
});
export type UserEditForm = z.infer<typeof userEditSchema>;
