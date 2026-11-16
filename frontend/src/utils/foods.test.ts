import type { Food } from '../api/types';
import { foodSchema } from '../validation/staff';
import { MICRONUTRIENTS, OPTIONAL_NUTRIENTS, OTHER_NUTRIENTS, knownNutrients } from './foods';

const valid = {
  name: 'Lentejas',
  category: 'legumes',
  calories: 352,
  proteinsG: 24.6,
  carbsG: 63,
  fatsG: 1.1,
  sugarsG: 2,
  ironMg: 6.5,
};

const messages = (input: object) => {
  const result = foodSchema.safeParse(input);
  return result.success
    ? {}
    : Object.fromEntries(result.error.issues.map((issue) => [issue.path.join('.'), issue.message]));
};

describe('food schema (same rules as the backend)', () => {
  it('accepts a food with only some optional nutrients', () => {
    expect(foodSchema.safeParse(valid).success).toBe(true);
    expect(foodSchema.safeParse({ ...valid, vitaminCMg: null }).success).toBe(true);
  });

  it('requires the name, category, calories and macros', () => {
    expect(messages({ name: '' })).toMatchObject({
      name: 'validation.required',
      category: 'validation.required',
      calories: 'validation.required',
      proteinsG: 'validation.required',
    });
  });

  it('checks ranges and the relations between nutrients', () => {
    expect(messages({ ...valid, calories: 901 })).toEqual({ calories: 'errors.max_value' });
    expect(messages({ ...valid, ironMg: -1 })).toEqual({ ironMg: 'errors.min_value' });
    expect(messages({ ...valid, proteinsG: 40, carbsG: 50, fatsG: 11 })).toEqual({
      fatsG: 'errors.macros_exceed_100g',
    });
    expect(messages({ ...valid, sugarsG: 70 })).toEqual({ sugarsG: 'errors.sugars_exceed_carbs' });
    expect(messages({ ...valid, saturatedFatG: 2 })).toEqual({
      saturatedFatG: 'errors.saturated_exceed_fats',
    });
  });
});

describe('nutrient helpers', () => {
  it('lists every optional nutrient once', () => {
    expect(OPTIONAL_NUTRIENTS).toHaveLength(OTHER_NUTRIENTS.length + MICRONUTRIENTS.length);
    expect(new Set(OPTIONAL_NUTRIENTS).size).toBe(OPTIONAL_NUTRIENTS.length);
  });

  it('keeps only the nutrients with a value, in display order', () => {
    const food = { ironMg: 6.5, sodiumMg: 0, calciumMg: null, vitaminB12Ug: null } as Food;
    expect(knownNutrients(food, MICRONUTRIENTS)).toEqual([
      ['sodiumMg', 'mg'],
      ['ironMg', 'mg'],
    ]);
  });
});
