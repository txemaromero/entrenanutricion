import { z } from './zod';

import { MEAL_KEYS } from '../utils/nutrition';

/** Same limits as the backend (`MAX_PORTION_GRAMS`, `MAX_MENU_ITEMS`). */
export const MAX_PORTION_GRAMS = 2000;
export const MAX_MENU_ITEMS = 60;

const grams = z
  .number({ error: 'validation.required' })
  .int('errors.invalid')
  .min(1, 'errors.min_value')
  .max(MAX_PORTION_GRAMS, 'errors.max_value');

export const portionSchema = z.object({ grams });
export type PortionForm = z.infer<typeof portionSchema>;

export const menuSchema = z.object({
  items: z
    .array(z.object({ meal: z.enum(MEAL_KEYS), foodId: z.number(), grams }))
    .max(MAX_MENU_ITEMS, 'errors.max_value'),
});
export type MenuForm = z.infer<typeof menuSchema>;
