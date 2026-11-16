import {
  ONBOARDING_DEFAULTS,
  toKg,
  toOnboardingPayload,
  validateStep,
  type OnboardingForm,
} from './onboarding';
import { maskDisplayDate, registerSchema } from './schemas';

const complete: OnboardingForm = {
  ...ONBOARDING_DEFAULTS,
  heightCm: 172,
  initialWeightKg: 80,
  goal: 'lose_weight',
  weeklyTrainingDays: 3,
  dailyTrainingTime: '1_2h',
  targetChange: 11,
  targetUnit: 'lbs',
  physicalActivityLevel: 'light',
  usualExerciseTypes: ['cardio'],
  availableEquipment: ['full_gym'],
  dietType: 'omnivore',
  foodRestrictions: ['none'],
  customFoodRestrictions: '',
  mealsPerDay: 4,
  macronutrientIntakeSelfAssessment: 'balanced',
  medicalConditions: ['none'],
  customMedicalCondition: '',
  supplements: ['none'],
  trainingPreference: 'gym',
  preferencesText: '',
};

describe('onboarding steps', () => {
  it('accepts a complete form at every step', () => {
    [0, 1, 2, 3, 4, 5].forEach((step) => expect(validateStep(step, complete)).toEqual({}));
  });

  it('checks height and weight ranges', () => {
    expect(validateStep(0, { ...complete, heightCm: 99, initialWeightKg: 301 })).toEqual({
      heightCm: 'errors.min_value',
      initialWeightKg: 'errors.max_value',
    });
    expect(validateStep(0, { ...complete, heightCm: undefined })).toEqual({
      heightCm: 'validation.required',
    });
  });

  it('requires a weight change unless the goal is to maintain', () => {
    expect(validateStep(1, { ...complete, targetChange: undefined })).toEqual({
      targetChange: 'validation.required',
    });
    expect(validateStep(1, { ...complete, goal: 'maintain', targetChange: undefined })).toEqual({});
  });

  it('rejects target weights out of range', () => {
    expect(
      validateStep(1, { ...complete, targetChange: 60, targetUnit: 'kg', initialWeightKg: 80 }),
    ).toEqual({ targetChange: 'errors.out_of_range' });
  });

  it('requires at least one option in multi-selects', () => {
    expect(validateStep(2, { ...complete, usualExerciseTypes: [] })).toEqual({
      usualExerciseTypes: 'errors.min_length',
    });
  });

  it('asks for a description of restrictions and of "other" conditions', () => {
    expect(validateStep(3, { ...complete, foodRestrictions: ['allergies'] })).toEqual({
      customFoodRestrictions: 'validation.required',
    });
    expect(validateStep(4, { ...complete, medicalConditions: ['other'] })).toEqual({
      customMedicalCondition: 'validation.required',
    });
  });

  it('converts pounds to kilograms in the payload', () => {
    expect(toKg(11, 'lbs')).toBe(5);
    const payload = toOnboardingPayload(complete);
    expect(payload.targetWeightChangeKg).toBe(5);
    expect(payload.diet.mealsPerDay).toBe(4);
    expect(payload.health.supplements).toEqual(['none']);
    expect(toOnboardingPayload({ ...complete, goal: 'maintain' }).targetWeightChangeKg).toBe(0);
  });
});

describe('registration form', () => {
  const schema = registerSchema(() => new Date(2026, 5, 15));
  const valid = {
    firstName: 'María José',
    lastName: 'Núñez',
    email: 'maria@example.com',
    password: 'Str0ng#Pass',
    birthDate: '10/03/1995',
    gender: 'F',
    termsAccepted: true,
    healthDataConsent: true,
  };

  it('accepts valid data', () => {
    expect(schema.safeParse(valid).success).toBe(true);
  });

  it('requires the terms and a gender', () => {
    const result = schema.safeParse({ ...valid, termsAccepted: false, gender: undefined });
    const messages = result.success ? [] : result.error.issues.map((issue) => issue.message);
    expect(messages).toEqual(
      expect.arrayContaining(['errors.terms_required', 'validation.required']),
    );
  });

  it('requires the explicit consent for health data', () => {
    const result = schema.safeParse({ ...valid, healthDataConsent: false });
    const messages = result.success ? [] : result.error.issues.map((issue) => issue.message);
    expect(messages).toEqual(['errors.health_consent_required']);
  });

  it('masks dates as dd/mm/aaaa while typing', () => {
    expect(maskDisplayDate('1')).toBe('1');
    expect(maskDisplayDate('1003')).toBe('10/03');
    expect(maskDisplayDate('10031995')).toBe('10/03/1995');
    expect(maskDisplayDate('10/03/19951')).toBe('10/03/1995');
    expect(maskDisplayDate('ab10c')).toBe('10');
  });
});
