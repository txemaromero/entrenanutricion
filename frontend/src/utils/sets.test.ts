import i18n from 'i18next';

import { setsSchema } from '../validation/training';
import { formatSets, initialSets, newRecordsText } from './sets';

describe('sets', () => {
  const t = () => i18n.getFixedT('es');

  it('formats sets with and without load', () => {
    expect(
      formatSets(
        t(),
        [
          { reps: 10, weightKg: 42.5 },
          { reps: 8, weightKg: null },
        ],
        'es',
      ),
    ).toBe('10 × 42,5 kg · 8 rep.');
  });

  it('announces the records a workout has just beaten', () => {
    expect(newRecordsText(t(), [], 'es')).toBe('');
    expect(
      newRecordsText(
        t(),
        [{ exerciseId: 1, exerciseName: 'Sentadilla', weightKg: 60, reps: 8 }],
        'es',
      ),
    ).toBe('¡Nuevo récord! Sentadilla: 8 × 60 kg.');
    expect(
      newRecordsText(
        i18n.getFixedT('en'),
        [
          { exerciseId: 1, exerciseName: 'Squat', weightKg: 60, reps: 8 },
          { exerciseId: 2, exerciseName: 'Bench press', weightKg: 42.5, reps: 6 },
        ],
        'en',
      ),
    ).toBe('New records! Squat: 8 × 60 kg, Bench press: 6 × 42.5 kg.');
  });

  it('prefills the plan with the loads of the last session', () => {
    const last = [
      { reps: 10, weightKg: 40 },
      { reps: 9, weightKg: 42.5 },
    ];
    expect(initialSets(3, 10, [], last)).toEqual([
      { reps: 10, weightKg: 40 },
      { reps: 10, weightKg: 42.5 },
      { reps: 10, weightKg: 42.5 },
    ]);
    expect(initialSets(2, 12, [], null)).toEqual([
      { reps: 12, weightKg: null },
      { reps: 12, weightKg: null },
    ]);
    const logged = [{ reps: 6, weightKg: 50 }];
    expect(initialSets(3, 10, logged, last)).toBe(logged);
  });

  it('validates like the backend', () => {
    const valid = (sets: unknown) => setsSchema.safeParse({ sets }).success;
    expect(valid([{ reps: 10, weightKg: 42.5 }, { reps: 8 }])).toBe(true);
    expect(valid([])).toBe(false);
    expect(valid([{ reps: 201 }])).toBe(false);
    expect(valid([{ reps: 10, weightKg: -1 }])).toBe(false);
    expect(valid([{ reps: 10, weightKg: 42.25 }])).toBe(false);
    expect(valid(Array.from({ length: 21 }, () => ({ reps: 10 })))).toBe(false);
  });
});
