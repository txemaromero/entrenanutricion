import { z } from './zod';

import type { Onboarding } from '../api/types';

/** Onboarding wizard (US-04): one schema per step, same ranges and rules as the backend. */

export const LBS_TO_KG = 0.45359237;

const number = (min: number, max: number, int = false) => {
  const base = z.number({ error: 'validation.required' });
  return (int ? base.int('errors.invalid') : base)
    .min(min, 'errors.min_value')
    .max(max, 'errors.max_value');
};

const multi = <T extends readonly [string, ...string[]]>(values: T) =>
  z.array(z.enum(values)).min(1, 'errors.min_length');

const choice = <T extends readonly [string, ...string[]]>(values: T) =>
  z.enum(values, { error: 'validation.required' });

export const GOALS = ['lose_weight', 'gain_muscle', 'maintain'] as const;
export const ACTIVITY_LEVELS = ['sedentary', 'light', 'moderate', 'intense'] as const;
export const DAILY_TIMES = ['lt_1h', '1_2h', 'gt_2h'] as const;
export const EXERCISE_TYPES = ['cardio', 'strength', 'flexibility', 'circuit', 'other'] as const;
export const EQUIPMENT = [
  'full_gym',
  'free_weights',
  'cardio_machines',
  'no_equipment',
  'other',
] as const;
export const DIET_TYPES = [
  'omnivore',
  'vegetarian',
  'vegan',
  'low_carb',
  'high_protein',
  'other',
] as const;
export const FOOD_RESTRICTIONS = [
  'allergies',
  'intolerances',
  'dietary_preferences',
  'none',
] as const;
export const MACRO_ASSESSMENTS = [
  'low_protein',
  'low_carbs',
  'low_fats',
  'balanced',
  'unknown',
] as const;
export const MEDICAL_CONDITIONS = [
  'diabetes',
  'hypertension',
  'joint_problems',
  'other',
  'none',
] as const;
export const SUPPLEMENTS = ['protein', 'multivitamin', 'omega3', 'other', 'none'] as const;
export const TRAINING_PREFERENCES = ['home', 'gym', 'outdoor', 'group_classes', 'other'] as const;

export const toKg = (value: number, unit: 'kg' | 'lbs'): number =>
  Math.round((unit === 'lbs' ? value * LBS_TO_KG : value) * 10) / 10;

const personal = z.object({
  heightCm: number(100, 250, true),
  initialWeightKg: number(30, 300),
});

const goals = z
  .object({
    initialWeightKg: z.number().optional(),
    goal: choice(GOALS),
    weeklyTrainingDays: number(1, 6, true),
    dailyTrainingTime: choice(DAILY_TIMES),
    targetChange: z.number().min(0, 'errors.min_value').optional(),
    targetUnit: z.enum(['kg', 'lbs']),
  })
  .superRefine((data, context) => {
    if (data.goal === 'maintain') return;
    const change = toKg(data.targetChange ?? 0, data.targetUnit);
    if (!change || change <= 0) {
      context.addIssue({ code: 'custom', path: ['targetChange'], message: 'validation.required' });
      return;
    }
    if (change > 100) {
      context.addIssue({ code: 'custom', path: ['targetChange'], message: 'errors.max_value' });
      return;
    }
    if (data.initialWeightKg) {
      const target =
        data.goal === 'lose_weight' ? data.initialWeightKg - change : data.initialWeightKg + change;
      if (target < 30 || target > 300) {
        context.addIssue({
          code: 'custom',
          path: ['targetChange'],
          message: 'errors.out_of_range',
        });
      }
    }
  });

const activity = z.object({
  physicalActivityLevel: choice(ACTIVITY_LEVELS),
  usualExerciseTypes: multi(EXERCISE_TYPES),
  availableEquipment: multi(EQUIPMENT),
});

const diet = z
  .object({
    dietType: choice(DIET_TYPES),
    foodRestrictions: multi(FOOD_RESTRICTIONS),
    customFoodRestrictions: z.string().max(1000, 'errors.max_length'),
    mealsPerDay: number(1, 10, true),
    macronutrientIntakeSelfAssessment: choice(MACRO_ASSESSMENTS),
  })
  .superRefine((data, context) => {
    const needsText = data.foodRestrictions.some((item) => item !== 'none');
    if (needsText && !data.customFoodRestrictions.trim()) {
      context.addIssue({
        code: 'custom',
        path: ['customFoodRestrictions'],
        message: 'validation.required',
      });
    }
  });

const health = z
  .object({
    medicalConditions: multi(MEDICAL_CONDITIONS),
    customMedicalCondition: z.string().max(1000, 'errors.max_length'),
    supplements: multi(SUPPLEMENTS),
  })
  .superRefine((data, context) => {
    if (data.medicalConditions.includes('other') && !data.customMedicalCondition.trim()) {
      context.addIssue({
        code: 'custom',
        path: ['customMedicalCondition'],
        message: 'validation.required',
      });
    }
  });

const preferences = z.object({
  trainingPreference: choice(TRAINING_PREFERENCES),
  preferencesText: z.string().max(1000, 'errors.max_length'),
});

export const ONBOARDING_STEPS = [
  { key: 'personal', schema: personal },
  { key: 'goals', schema: goals },
  { key: 'activity', schema: activity },
  { key: 'diet', schema: diet },
  { key: 'health', schema: health },
  { key: 'preferences', schema: preferences },
] as const;

export interface OnboardingForm {
  heightCm?: number;
  initialWeightKg?: number;
  goal?: Onboarding['goal'];
  weeklyTrainingDays?: number;
  dailyTrainingTime?: Onboarding['dailyTrainingTime'];
  targetChange?: number;
  targetUnit: 'kg' | 'lbs';
  physicalActivityLevel?: Onboarding['physicalActivityLevel'];
  usualExerciseTypes: Onboarding['usualExerciseTypes'];
  availableEquipment: Onboarding['availableEquipment'];
  dietType?: Onboarding['diet']['dietType'];
  foodRestrictions: Onboarding['diet']['foodRestrictions'];
  customFoodRestrictions: string;
  mealsPerDay?: number;
  macronutrientIntakeSelfAssessment?: Onboarding['diet']['macronutrientIntakeSelfAssessment'];
  medicalConditions: Onboarding['health']['medicalConditions'];
  customMedicalCondition: string;
  supplements: Onboarding['health']['supplements'];
  trainingPreference?: Onboarding['trainingPreference'];
  preferencesText: string;
}

export const ONBOARDING_DEFAULTS: OnboardingForm = {
  targetUnit: 'kg',
  weeklyTrainingDays: 3,
  mealsPerDay: 4,
  usualExerciseTypes: [],
  availableEquipment: [],
  foodRestrictions: [],
  customFoodRestrictions: '',
  medicalConditions: [],
  customMedicalCondition: '',
  supplements: [],
  preferencesText: '',
};

/** Issues of one step as {field: i18n key}. Empty object when the step is valid. */
export const validateStep = (step: number, values: OnboardingForm): Record<string, string> => {
  const result = ONBOARDING_STEPS[step].schema.safeParse(values);
  if (result.success) return {};
  return Object.fromEntries(
    result.error.issues.map((issue) => [String(issue.path[0]), issue.message]),
  );
};

export const toOnboardingPayload = (values: OnboardingForm): Onboarding => {
  const goal = values.goal!;
  return {
    heightCm: values.heightCm!,
    initialWeightKg: values.initialWeightKg!,
    goal,
    targetWeightChangeKg:
      goal === 'maintain' ? 0 : toKg(values.targetChange ?? 0, values.targetUnit),
    weeklyTrainingDays: values.weeklyTrainingDays!,
    dailyTrainingTime: values.dailyTrainingTime!,
    physicalActivityLevel: values.physicalActivityLevel!,
    usualExerciseTypes: values.usualExerciseTypes,
    availableEquipment: values.availableEquipment,
    trainingPreference: values.trainingPreference!,
    preferencesText: values.preferencesText,
    diet: {
      dietType: values.dietType!,
      foodRestrictions: values.foodRestrictions,
      customFoodRestrictions: values.customFoodRestrictions,
      mealsPerDay: values.mealsPerDay!,
      macronutrientIntakeSelfAssessment: values.macronutrientIntakeSelfAssessment!,
    },
    health: {
      medicalConditions: values.medicalConditions,
      customMedicalCondition: values.customMedicalCondition,
      supplements: values.supplements,
    },
  };
};
