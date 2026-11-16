import type { Nutrients } from '../api/types';
import { formatNumber } from '../i18n/format';

/** Live kcal from macros and the ±10 % check (mirrors the backend). */

export const MEAL_KEYS = ['breakfast', 'lunch', 'dinner', 'snacks'] as const;
export const KCAL_PER_GRAM = { proteins: 4, carbs: 4, fats: 9 } as const;
export const CALORIES_TOLERANCE = 0.1;

export const macrosKcal = (proteinsG = 0, carbsG = 0, fatsG = 0): number =>
  proteinsG * KCAL_PER_GRAM.proteins + carbsG * KCAL_PER_GRAM.carbs + fatsG * KCAL_PER_GRAM.fats;

export const caloriesMismatch = (
  calories: number | undefined,
  proteinsG?: number,
  carbsG?: number,
  fatsG?: number,
): boolean => {
  const total = macrosKcal(proteinsG, carbsG, fatsG);
  if (!calories || !total) return false;
  return Math.abs(calories - total) > total * CALORIES_TOLERANCE;
};

export const distributionSum = (
  distribution: Partial<Record<(typeof MEAL_KEYS)[number], number>>,
) => MEAL_KEYS.reduce((total, key) => total + (Number(distribution[key]) || 0), 0);

/** "450 g" or, from a kilo, "1,1 kg". */
export const formatGrams = (grams: number, language: string): string =>
  grams >= 1000
    ? `${formatNumber(grams / 1000, language, { maximumFractionDigits: 1 })} kg`
    : `${formatNumber(grams, language, { maximumFractionDigits: 0 })} g`;

export const EMPTY_NUTRIENTS: Nutrients = { calories: 0, proteinsG: 0, carbsG: 0, fatsG: 0 };

/** Values of `grams` of a food given per 100 g (one decimal, like the backend). */
export const portionOf = (per100: Nutrients, grams: number): Nutrients => ({
  calories: Math.round(per100.calories * grams) / 100,
  proteinsG: Math.round(per100.proteinsG * grams) / 100,
  carbsG: Math.round(per100.carbsG * grams) / 100,
  fatsG: Math.round(per100.fatsG * grams) / 100,
});

/** Per 100 g from a portion (to recompute a row whose grams change). */
export const per100Of = (portion: Nutrients, grams: number): Nutrients =>
  grams > 0
    ? {
        calories: (portion.calories * 100) / grams,
        proteinsG: (portion.proteinsG * 100) / grams,
        carbsG: (portion.carbsG * 100) / grams,
        fatsG: (portion.fatsG * 100) / grams,
      }
    : EMPTY_NUTRIENTS;

export const sumNutrients = (rows: Nutrients[]): Nutrients =>
  rows.reduce(
    (total, row) => ({
      calories: total.calories + row.calories,
      proteinsG: total.proteinsG + row.proteinsG,
      carbsG: total.carbsG + row.carbsG,
      fatsG: total.fatsG + row.fatsG,
    }),
    EMPTY_NUTRIENTS,
  );

/** Deviation in % of `value` from `target` (null without a target). */
export const deviationPct = (value: number, target: number | null | undefined): number | null =>
  target ? Math.round(((value - target) * 1000) / target) / 10 : null;
