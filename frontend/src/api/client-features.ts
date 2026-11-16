import { withOfflineCopy } from '../offline/store';
import { api } from './client';
import type {
  BadgesOverview,
  CompleteWorkoutResult,
  Dashboard,
  DayProgress,
  Exercise,
  ExerciseHistory,
  MyNutritionPlan,
  MyTrainingPlan,
  DiaryDay,
  DiarySummary,
  Meal,
  Menu,
  Note,
  Paginated,
  PersonalRecord,
  Reminders,
  ShoppingList,
  SetEntry,
  TrainingDays,
  TrainingStats,
  WeightSummary,
  WorkoutDay,
  WorkoutSession,
} from './types';

/** Endpoints of the client's own area (`/me/...`). */

/** Notes with the professional team (they need a connection). */
export const notesApi = {
  list: () => api.get<Paginated<Note>>('/me/notes', { params: { limit: 100 } }).then((r) => r.data),
  send: (body: string) => api.post<Note>('/me/notes', { body }).then((r) => r.data),
  unread: () => api.get<{ unread: number }>('/me/notes/unread').then((r) => r.data.unread),
  markRead: () => api.post('/me/notes/read'),
};

export const remindersApi = {
  get: () => api.get<Reminders>('/me/reminders').then((r) => r.data),
  /** `trainingTime` null restores the default time. */
  update: (enabled: boolean, trainingTime: string | null) =>
    api.put<Reminders>('/me/reminders', { enabled, trainingTime }).then((r) => r.data),
};

export const trainingApi = {
  // The plan, the workouts and the exercises also work without coverage (last copy).
  myPlan: withOfflineCopy('training-plan', () =>
    api.get<MyTrainingPlan>('/me/training-plan').then((r) => r.data),
  ),

  workoutDay: (id: number) =>
    withOfflineCopy(`workout-${id}`, () =>
      api.get<WorkoutDay>(`/me/training-plan/workouts/${id}`).then((r) => r.data),
    )(),

  /** Mark an exercise (and, optionally, the sets done so far: omitted keeps the logged ones). */
  setExerciseDone: (workoutId: number, itemId: number, completed: boolean, sets?: SetEntry[]) =>
    api
      .put<{
        workoutExerciseId: number;
        completed: boolean;
        loggedSets: SetEntry[];
        progress: DayProgress;
      }>(`/me/training-plan/workouts/${workoutId}/exercises/${itemId}`, { completed, sets })
      .then((r) => r.data),

  records: () => api.get<PersonalRecord[]>('/me/records').then((r) => r.data),

  exerciseHistory: (exerciseId: number) =>
    withOfflineCopy(`history-${exerciseId}`, () =>
      api.get<ExerciseHistory>(`/me/exercises/${exerciseId}/history`).then((r) => r.data),
    )(),

  completeWorkout: (workoutId: number) =>
    api
      .post<CompleteWorkoutResult>(`/me/training-plan/workouts/${workoutId}/complete`)
      .then((r) => r.data),

  exercise: (id: number) =>
    withOfflineCopy(`exercise-${id}`, () =>
      api.get<Exercise>(`/me/exercises/${id}`).then((r) => r.data),
    )(),

  /** Pick the weekdays to train on; an empty list restores the recommended days. */
  setTrainingDays: (days: number[]) =>
    api.put<TrainingDays>('/me/training-days', { days }).then((r) => r.data),
};

export const nutritionApi = {
  myPlan: () => api.get<MyNutritionPlan>('/me/nutrition-plan').then((r) => r.data),
  // The menu and the shopping list also work without coverage (last copy).
  menu: withOfflineCopy('nutrition-menu', () =>
    api.get<Menu>('/me/nutrition-plan/menu').then((r) => r.data),
  ),
  shoppingList: (days: number) =>
    withOfflineCopy(`shopping-list-${days}`, () =>
      api.get<ShoppingList>('/me/shopping-list', { params: { days } }).then((r) => r.data),
    )(),
};

/** Food diary: every change returns the whole day with its totals. */
export const foodLogApi = {
  day: (date: string) =>
    api.get<DiaryDay>('/me/food-log', { params: { date } }).then((r) => r.data),
  add: (input: { date: string; meal: Meal; foodId: number; grams: number }) =>
    api.post<DiaryDay>('/me/food-log', input).then((r) => r.data),
  update: (id: number, input: { grams?: number; meal?: Meal }) =>
    api.patch<DiaryDay>(`/me/food-log/${id}`, input).then((r) => r.data),
  remove: (id: number) => api.delete<DiaryDay>(`/me/food-log/${id}`).then((r) => r.data),
  /** Log the menu of one meal or, without `meal`, of the whole day. */
  copyMenu: (date: string, meal?: Meal) =>
    api.post<DiaryDay>('/me/food-log/copy-menu', { date, meal }).then((r) => r.data),
  summary: (days = 7) =>
    api.get<DiarySummary>('/me/food-log/summary', { params: { days } }).then((r) => r.data),
};

export interface HistoryFilters {
  from?: string;
  to?: string;
  workout?: number;
  limit?: number;
  offset?: number;
}

export const progressApi = {
  dashboard: (month?: string) =>
    api
      .get<Dashboard>('/me/progress/dashboard', { params: month ? { month } : {} })
      .then((r) => r.data),

  history: (filters: HistoryFilters = {}) =>
    api
      .get<Paginated<WorkoutSession>>('/me/progress/history', {
        params: Object.fromEntries(
          Object.entries({ limit: 50, ...filters }).filter(
            ([, value]) => value !== undefined && value !== '',
          ),
        ),
      })
      .then((r) => r.data),

  stats: () => api.get<TrainingStats>('/me/progress/stats').then((r) => r.data),
  weights: () => api.get<WeightSummary>('/me/weight-records').then((r) => r.data),

  /** Badges with their progress; pending ones are awarded on the way. */
  badges: () => api.get<BadgesOverview>('/me/badges').then((r) => r.data),

  addWeight: (weightKg: number, date?: string) =>
    api.post<WeightSummary>('/me/weight-records', { weightKg, date }).then((r) => r.data),
};
