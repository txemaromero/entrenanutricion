import type { TFunction } from 'i18next';

import type { NewRecord, SetEntry } from '../api/types';
import { formatNumber } from '../i18n/format';

/** "10 × 40 kg" or, without load, "10 rep.". */
export const formatSet = (t: TFunction, entry: SetEntry, language: string): string =>
  entry.weightKg !== null && entry.weightKg !== undefined
    ? t('sets.repsByWeight', { reps: entry.reps, weight: formatNumber(entry.weightKg, language) })
    : t('sets.repsOnly', { reps: entry.reps });

export const formatSets = (t: TFunction, sets: SetEntry[], language: string): string =>
  sets.map((entry) => formatSet(t, entry, language)).join(' · ');

/** "New record! Squat: 8 × 60 kg" for the records a workout has just beaten ('' when none). */
export const newRecordsText = (t: TFunction, records: NewRecord[] | undefined, language: string) =>
  records?.length
    ? t('sets.newRecord', {
        count: records.length,
        list: records
          .map((record) =>
            t('sets.recordItem', {
              name: record.exerciseName,
              weight: formatNumber(record.weightKg, language),
              reps: record.reps,
            }),
          )
          .join(', '),
      })
    : '';

/** Rows of the editor: the logged sets or, if none, the planned ones with last session's load. */
export const initialSets = (
  planned: number,
  plannedReps: number,
  logged: SetEntry[],
  last: SetEntry[] | null,
): SetEntry[] =>
  logged.length
    ? logged
    : Array.from({ length: planned }, (_, index) => ({
        reps: plannedReps,
        weightKg: last?.[index]?.weightKg ?? last?.[last.length - 1]?.weightKg ?? null,
      }));
