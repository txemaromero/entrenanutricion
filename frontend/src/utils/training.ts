import type { TFunction } from 'i18next';

import type { DayExercise, Motivation } from '../api/types';
import { formatNumber } from '../i18n/format';

/** % of the day = ticked exercises / exercises of the workout. */
export const dayProgress = (exercises: Pick<DayExercise, 'completed'>[]) => {
  const total = exercises.length;
  const completed = exercises.filter((exercise) => exercise.completed).length;
  return { completed, total, percent: total ? Math.round((completed * 100) / total) : 0 };
};

/** Numeric parameters of motivation messages, formatted for the language. */
export const motivationParams = (motivation: Motivation, language: string) =>
  Object.fromEntries(
    Object.entries(motivation.params).map(([key, value]) => [key, formatNumber(value, language)]),
  );

export const motivationText = (t: TFunction, motivation: Motivation, language: string): string =>
  motivation.keys.map((key) => t(key, motivationParams(motivation, language))).join(' ');
