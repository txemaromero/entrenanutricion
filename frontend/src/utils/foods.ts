import type { Food } from '../api/types';

/** Same order and units as the backend (`apps.nutrition.models`). */
export const FOOD_CATEGORIES = [
  'vegetables',
  'fruits',
  'grains',
  'legumes',
  'meat',
  'fish',
  'eggs',
  'dairy',
  'nuts_seeds',
  'fats_oils',
  'other',
] as const;

export type NutrientKey =
  | 'fiberG'
  | 'sugarsG'
  | 'saturatedFatG'
  | 'sodiumMg'
  | 'potassiumMg'
  | 'calciumMg'
  | 'ironMg'
  | 'magnesiumMg'
  | 'vitaminAUg'
  | 'vitaminCMg'
  | 'vitaminDUg'
  | 'vitaminB12Ug';

export const OTHER_NUTRIENTS: [NutrientKey, string][] = [
  ['fiberG', 'g'],
  ['sugarsG', 'g'],
  ['saturatedFatG', 'g'],
];

export const MICRONUTRIENTS: [NutrientKey, string][] = [
  ['sodiumMg', 'mg'],
  ['potassiumMg', 'mg'],
  ['calciumMg', 'mg'],
  ['ironMg', 'mg'],
  ['magnesiumMg', 'mg'],
  ['vitaminAUg', 'µg'],
  ['vitaminCMg', 'mg'],
  ['vitaminDUg', 'µg'],
  ['vitaminB12Ug', 'µg'],
];

export const OPTIONAL_NUTRIENTS = [...OTHER_NUTRIENTS, ...MICRONUTRIENTS].map(([key]) => key);

/** Nutrients of `food` that have a value, in display order. */
export const knownNutrients = (food: Food, nutrients: [NutrientKey, string][]) =>
  nutrients.filter(([key]) => food[key] !== null && food[key] !== undefined);
