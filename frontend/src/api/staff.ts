import { api } from './client';
import type {
  AdherenceList,
  AdherenceRow,
  AdherenceStatus,
  ClientAdherence,
  DiarySummary,
  Exercise,
  ExerciseInput,
  ExerciseMedia,
  ExerciseSummary,
  GrowthRow,
  PlanPopularityRow,
  MealPlan,
  MealPlanCategory,
  MealPlanInput,
  MealPlanSummary,
  Menu,
  MenuItemInput,
  MuscleGroup,
  Note,
  NotesInboxEntry,
  Paginated,
  PendingUser,
  PopularityRow,
  Role,
  StatisticsSummary,
  TrainingPlan,
  TrainingPlanInput,
  TrainingPlanSummary,
  UserCreateInput,
  UserDetail,
  UserSummary,
  UserUpdateInput,
  Workout,
  WorkoutInput,
  WorkoutSummary,
} from './types';

/** Endpoints of the management area (trainers, nutritionists and admins). */

export interface ListParams {
  search?: string;
  limit?: number;
  offset?: number;
}

const list = <T, R extends Paginated<T> = Paginated<T>>(url: string, params: object = {}) =>
  api
    .get<R>(url, {
      params: Object.fromEntries(
        Object.entries({ limit: 100, ...params } as Record<string, unknown>).filter(
          ([, value]) => value !== undefined && value !== '',
        ),
      ),
    })
    .then((r) => r.data);

const formWith = (field: string, file: Blob, filename: string, extra: object = {}) => {
  const form = new FormData();
  form.append(field, file, filename);
  Object.entries(extra).forEach(([key, value]) => form.append(key, String(value)));
  return form;
};

/** Generic catalog resource with the single-media endpoints of workouts and plans. */
const resource = <Summary, Detail, Input>(base: string) => ({
  list: (params: ListParams = {}) => list<Summary>(base, params),
  get: (id: number) => api.get<Detail>(`${base}/${id}`).then((r) => r.data),
  create: (input: Input) => api.post<Detail>(base, input).then((r) => r.data),
  update: (id: number, input: Input) => api.put<Detail>(`${base}/${id}`, input).then((r) => r.data),
  remove: (id: number) => api.delete(`${base}/${id}`),
});

const withMedia = (base: string) => ({
  setMedia: (id: number, file: Blob, filename: string) =>
    api.put(`${base}/${id}/media`, formWith('media', file, filename)),
  removeMedia: (id: number) => api.delete(`${base}/${id}/media`),
});

export const catalogApi = {
  muscleGroups: () => api.get<MuscleGroup[]>('/muscle-groups').then((r) => r.data),
  exercises: {
    ...resource<ExerciseSummary, Exercise, ExerciseInput>('/exercises'),
    addMedia: (id: number, file: Blob, filename: string) =>
      api
        .post<ExerciseMedia>(`/exercises/${id}/media`, formWith('file', file, filename))
        .then((r) => r.data),
    removeMedia: (id: number, mediaId: number) => api.delete(`/exercises/${id}/media/${mediaId}`),
  },
  workouts: {
    ...resource<WorkoutSummary, Workout, WorkoutInput>('/workouts'),
    ...withMedia('/workouts'),
  },
  plans: {
    ...resource<TrainingPlanSummary, TrainingPlan, TrainingPlanInput>('/training-plans'),
    ...withMedia('/training-plans'),
  },
};

export const mealPlansApi = {
  ...resource<MealPlanSummary, MealPlan, MealPlanInput>('/meal-plans'),
  menu: (id: number) => api.get<Menu>(`/meal-plans/${id}/menu`).then((r) => r.data),
  /** Replaces the whole sample day menu. */
  setMenu: (id: number, items: MenuItemInput[]) =>
    api.put<Menu>(`/meal-plans/${id}/menu`, { items }).then((r) => r.data),
  list: (params: ListParams & { category?: MealPlanCategory } = {}) =>
    list<MealPlanSummary>('/meal-plans', params),
};

export const usersApi = {
  list: (params: ListParams & { role?: Role | '' } = {}) => list<UserSummary>('/users', params),
  get: (id: number) => api.get<UserDetail>(`/users/${id}`).then((r) => r.data),
  create: (input: UserCreateInput) => api.post<UserDetail>('/users', input).then((r) => r.data),
  update: (id: number, input: UserUpdateInput) =>
    api.patch<UserDetail>(`/users/${id}`, input).then((r) => r.data),
  uploadPhoto: (id: number, file: Blob, filename: string) =>
    api.patch<UserDetail>(`/users/${id}`, formWith('photo', file, filename)).then((r) => r.data),
  remove: (id: number) => api.delete(`/users/${id}`),
  foodLogSummary: (id: number, days = 7) =>
    api
      .get<DiarySummary>(`/users/${id}/food-log/summary`, { params: { days } })
      .then((r) => r.data),
};

export const adherenceApi = {
  list: (params: ListParams & { status?: AdherenceStatus | '' } = {}) =>
    list<AdherenceRow, AdherenceList>('/adherence', params),
  client: (userId: number) =>
    api.get<ClientAdherence>(`/users/${userId}/adherence`).then((r) => r.data),
};

export const staffNotesApi = {
  list: (userId: number) => list<Note>(`/users/${userId}/notes`),
  send: (userId: number, body: string) =>
    api.post<Note>(`/users/${userId}/notes`, { body }).then((r) => r.data),
  markRead: (userId: number) => api.post(`/users/${userId}/notes/read`),
  inbox: () => api.get<NotesInboxEntry[]>('/notes/inbox').then((r) => r.data),
};

export const assignmentsApi = {
  pending: (params: ListParams = {}) => list<PendingUser>('/assignments/pending', params),
  assignTraining: (userId: number, planId: number, replace = false) =>
    api.post(`/users/${userId}/assign-training-plan`, { planId, replace }).then((r) => r.data),
  assignNutrition: (userId: number, planId: number, replace = false) =>
    api.post(`/users/${userId}/assign-nutrition-plan`, { planId, replace }).then((r) => r.data),
};

export const statisticsApi = {
  summary: () => api.get<StatisticsSummary>('/statistics/summary').then((r) => r.data),
  years: () => api.get<{ years: number[] }>('/statistics/years').then((r) => r.data.years),
  popularity: (year: number, limit = 10) =>
    api
      .get<{ year: number; results: PopularityRow[] }>('/statistics/exercise-popularity', {
        params: { year, limit },
      })
      .then((r) => r.data.results),
  growth: (year: number) =>
    api
      .get<{ year: number; months: GrowthRow[] }>('/statistics/platform-growth', {
        params: { year },
      })
      .then((r) => r.data.months),
  sessions: (year: number) =>
    api
      .get<{ year: number; months: GrowthRow[] }>('/statistics/sessions', { params: { year } })
      .then((r) => r.data.months),
  planPopularity: () =>
    api
      .get<{ training: PlanPopularityRow[]; nutrition: PlanPopularityRow[] }>(
        '/statistics/plan-popularity',
      )
      .then((r) => r.data),
};
