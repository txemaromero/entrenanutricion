import { trainingApi } from '../api/client-features';
import { ApiError } from '../api/errors';
import type { DayExercise, WorkoutDay } from '../api/types';
import { saveExerciseMark } from './marks';
import { enqueueMark, pendingMarks } from './outbox';
import { offlineStore } from './store';

const exercise = (id: number): DayExercise => ({
  id,
  order: id,
  sets: 3,
  reps: 10,
  restSeconds: 60,
  completed: false,
  loggedSets: [],
  lastSets: null,
  exercise: { id: id * 100, name: `Exercise ${id}` } as DayExercise['exercise'],
});

const day = (): WorkoutDay =>
  ({
    id: 5,
    status: 'available',
    exercises: [exercise(1), exercise(2)],
    progress: { completed: 0, total: 2, percent: 0 },
  }) as unknown as WorkoutDay;

describe('exercise marks with sets', () => {
  beforeEach(() => {
    localStorage.clear();
    offlineStore.setOwner(7);
    vi.restoreAllMocks();
  });

  it('a later checkbox change keeps the sets logged offline', () => {
    const sets = [{ reps: 10, weightKg: 40 }];
    enqueueMark({ workoutId: 1, itemId: 10, completed: true, sets });
    enqueueMark({ workoutId: 1, itemId: 10, completed: false });

    expect(pendingMarks()).toEqual([{ workoutId: 1, itemId: 10, completed: false, sets }]);
  });

  it('saves online with the sets the API returns', async () => {
    const sets = [{ reps: 12, weightKg: 20 }];
    vi.spyOn(trainingApi, 'setExerciseDone').mockResolvedValue({
      workoutExerciseId: 1,
      completed: true,
      loggedSets: sets,
      progress: { completed: 1, total: 2, percent: 50 },
    });

    const result = await saveExerciseMark(day(), 1, true, sets);

    expect(trainingApi.setExerciseDone).toHaveBeenCalledWith(5, 1, true, sets);
    expect(result.queued).toBe(false);
    expect(result.day.exercises[0]).toMatchObject({ completed: true, loggedSets: sets });
    expect(result.day.progress.percent).toBe(50);
    expect(offlineStore.read<WorkoutDay>('workout-5')?.exercises[0].loggedSets).toEqual(sets);
  });

  it('queues the mark and the sets without coverage', async () => {
    const sets = [{ reps: 8, weightKg: null }];
    vi.spyOn(trainingApi, 'setExerciseDone').mockRejectedValue(
      new ApiError({ status: 0, code: 'network_error' }),
    );

    const result = await saveExerciseMark(day(), 2, true, sets);

    expect(result.queued).toBe(true);
    expect(result.day.progress).toEqual({ completed: 1, total: 2, percent: 50 });
    expect(pendingMarks()).toEqual([{ workoutId: 5, itemId: 2, completed: true, sets }]);
    expect(offlineStore.read<WorkoutDay>('workout-5')?.exercises[1].completed).toBe(true);
  });

  it('other errors reach the page and queue nothing', async () => {
    vi.spyOn(trainingApi, 'setExerciseDone').mockRejectedValue(
      new ApiError({ status: 409, code: 'workout_already_completed' }),
    );

    await expect(saveExerciseMark(day(), 1, true)).rejects.toMatchObject({
      code: 'workout_already_completed',
    });
    expect(pendingMarks()).toEqual([]);
  });
});
