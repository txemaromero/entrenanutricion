import { trainingApi } from '../api/client-features';
import type { SetEntry, WorkoutDay } from '../api/types';
import { dayProgress } from '../utils/training';
import { enqueueMark } from './outbox';
import { isNetworkError, offlineStore } from './store';

/** The day with one exercise (un)marked and, if given, its sets replaced. */
export const withMark = (
  day: WorkoutDay,
  itemId: number,
  completed: boolean,
  sets?: SetEntry[],
): WorkoutDay => {
  const exercises = day.exercises.map((exercise) =>
    exercise.id === itemId
      ? { ...exercise, completed, loggedSets: sets ?? exercise.loggedSets }
      : exercise,
  );
  return { ...day, exercises, progress: dayProgress(exercises) };
};

/**
 * Save a mark (and the sets) of an exercise. Without coverage it is queued and sent when the
 * connection returns; the offline copy of the day is updated so every screen shows it.
 */
export const saveExerciseMark = async (
  day: WorkoutDay,
  itemId: number,
  completed: boolean,
  sets?: SetEntry[],
): Promise<{ day: WorkoutDay; queued: boolean }> => {
  const marked = withMark(day, itemId, completed, sets);
  const key = `workout-${day.id}`;
  try {
    const result = await trainingApi.setExerciseDone(day.id, itemId, completed, sets);
    const saved = {
      ...withMark(day, itemId, completed, result.loggedSets),
      progress: result.progress,
    };
    offlineStore.write(key, saved);
    return { day: saved, queued: false };
  } catch (caught) {
    if (!isNetworkError(caught)) throw caught;
    enqueueMark({ workoutId: day.id, itemId, completed, sets });
    offlineStore.write(key, marked);
    return { day: marked, queued: true };
  }
};
