import { camelizeKeys, snakifyKeys, toCamel, toSnake } from './case';

describe('key case conversion', () => {
  it('converts single keys both ways', () => {
    expect(toCamel('initial_weight_kg')).toBe('initialWeightKg');
    expect(toSnake('initialWeightKg')).toBe('initial_weight_kg');
    expect(toCamel('1_2h')).toBe('1_2h');
  });

  it('keeps one-letter words and digits when going back to snake_case', () => {
    ['vitamin_a_ug', 'vitamin_b12_ug', 'vitamin_c_mg', 'saturated_fat_g'].forEach((key) =>
      expect(toSnake(toCamel(key))).toBe(key),
    );
    expect(toCamel('vitamin_a_ug')).toBe('vitaminAUg');
  });

  it('converts each segment of dotted error paths', () => {
    expect(toCamel('diet.meals_per_day')).toBe('diet.mealsPerDay');
    expect(toSnake('exercises.0.restSeconds')).toBe('exercises.0.rest_seconds');
  });

  it('converts nested objects and arrays but not values', () => {
    const payload = {
      user_status: 'pending_assignment',
      plan: { media_url: null },
      workouts: [{ rest_seconds: 60, exercise: { muscle_groups: [{ slug: 'lower_back' }] } }],
    };

    expect(camelizeKeys(payload)).toEqual({
      userStatus: 'pending_assignment',
      plan: { mediaUrl: null },
      workouts: [{ restSeconds: 60, exercise: { muscleGroups: [{ slug: 'lower_back' }] } }],
    });
    expect(snakifyKeys(camelizeKeys(payload))).toEqual(payload);
  });

  it('leaves FormData, dates and primitives untouched', () => {
    const form = new FormData();
    const date = new Date(2026, 0, 1);
    expect(snakifyKeys(form)).toBe(form);
    expect(snakifyKeys(date)).toBe(date);
    expect(camelizeKeys('text')).toBe('text');
  });
});
