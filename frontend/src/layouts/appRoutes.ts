import type { ComponentType } from 'react';

import type { Me } from '../api/types';
import { PATHS, isActiveClient } from '../auth/routing';

/**
 * Pages under /app, loaded on demand: each role downloads only its own screens (a client never
 * gets the management forms, and the staff never get the client's training screens). The pages
 * of a role are all loaded at once before the tabs are shown (`useRoleRoutes`), so Ionic's
 * router never has to wait for a page in the middle of a transition.
 */
type PageLoader = () => Promise<ComponentType>;

export interface AppRoute {
  path: string;
  load: PageLoader;
  exact?: boolean;
}

const page =
  <M>(load: () => Promise<M>, pick: (module: M) => ComponentType): PageLoader =>
  () =>
    load().then(pick);

const pages = {
  profile: page(
    () => import('../pages/shared/ProfilePage'),
    (m) => m.default,
  ),
  editProfile: page(
    () => import('../pages/shared/EditProfilePage'),
    (m) => m.default,
  ),
  planStatus: page(
    () => import('../pages/client/PlanStatusPage'),
    (m) => m.default,
  ),
  trainingPlan: page(
    () => import('../pages/client/TrainingPlanPage'),
    (m) => m.default,
  ),
  workoutDay: page(
    () => import('../pages/client/WorkoutDayPage'),
    (m) => m.default,
  ),
  exerciseDetail: page(
    () => import('../pages/client/ExerciseDetailPage'),
    (m) => m.default,
  ),
  nutrition: page(
    () => import('../pages/client/NutritionPage'),
    (m) => m.default,
  ),
  progress: page(
    () => import('../pages/client/ProgressPage'),
    (m) => m.default,
  ),
  badges: page(
    () => import('../pages/client/BadgesPage'),
    (m) => m.default,
  ),
  clientFoods: page(
    () => import('../pages/shared/FoodPages'),
    (m) => m.ClientFoodsPage,
  ),
  clientFood: page(
    () => import('../pages/shared/FoodPages'),
    (m) => m.ClientFoodDetailPage,
  ),
  catalog: page(
    () => import('../pages/trainer/CatalogPage'),
    (m) => m.default,
  ),
  workoutForm: page(
    () => import('../pages/trainer/WorkoutFormPage'),
    (m) => m.default,
  ),
  workoutDetail: page(
    () => import('../pages/trainer/CatalogDetailPages'),
    (m) => m.WorkoutDetailPage,
  ),
  exerciseForm: page(
    () => import('../pages/trainer/ExerciseFormPage'),
    (m) => m.default,
  ),
  exerciseStaff: page(
    () => import('../pages/trainer/CatalogDetailPages'),
    (m) => m.ExerciseDetailStaffPage,
  ),
  planForm: page(
    () => import('../pages/trainer/PlanFormPage'),
    (m) => m.default,
  ),
  planDetail: page(
    () => import('../pages/trainer/CatalogDetailPages'),
    (m) => m.PlanDetailPage,
  ),
  mealPlans: page(
    () => import('../pages/nutritionist/MealPlansPage'),
    (m) => m.default,
  ),
  mealPlanForm: page(
    () => import('../pages/nutritionist/MealPlanFormPage'),
    (m) => m.default,
  ),
  mealPlanDetail: page(
    () => import('../pages/nutritionist/MealPlanDetailPage'),
    (m) => m.default,
  ),
  staffFoods: page(
    () => import('../pages/shared/FoodPages'),
    (m) => m.StaffFoodsPage,
  ),
  staffFood: page(
    () => import('../pages/shared/FoodPages'),
    (m) => m.StaffFoodDetailPage,
  ),
  foodForm: page(
    () => import('../pages/nutritionist/FoodFormPage'),
    (m) => m.default,
  ),
  users: page(
    () => import('../pages/shared/UsersPage'),
    (m) => m.default,
  ),
  userDetail: page(
    () => import('../pages/shared/UserDetailPage'),
    (m) => m.default,
  ),
  foodDiary: page(
    () => import('../pages/client/FoodDiaryPage'),
    (m) => m.default,
  ),
  shoppingList: page(
    () => import('../pages/client/ShoppingListPage'),
    (m) => m.default,
  ),
  menuEditor: page(
    () => import('../pages/nutritionist/MenuEditorPage'),
    (m) => m.default,
  ),
  notes: page(
    () => import('../pages/client/NotesPage'),
    (m) => m.default,
  ),
  adherence: page(
    () => import('../pages/shared/AdherencePage'),
    (m) => m.default,
  ),
  assignments: page(
    () => import('../pages/shared/AssignmentsPage'),
    (m) => m.default,
  ),
  assignmentDetail: page(
    () => import('../pages/shared/AssignmentDetailPage'),
    (m) => m.default,
  ),
  statistics: page(
    () => import('../pages/admin/StatisticsPage'),
    (m) => m.default,
  ),
  userCreate: page(
    () => import('../pages/admin/UserFormPages'),
    (m) => m.UserCreatePage,
  ),
  userEdit: page(
    () => import('../pages/admin/UserFormPages'),
    (m) => m.UserEditPage,
  ),
};

const route = (path: string, load: PageLoader): AppRoute => ({ path, load, exact: true });

const PROFILE = [
  route(PATHS.profile, pages.profile),
  route(`${PATHS.profile}/edit`, pages.editProfile),
];

const CLIENT_PENDING = [
  route(PATHS.status, pages.planStatus),
  route(PATHS.notes, pages.notes),
  ...PROFILE,
];

const CLIENT_ACTIVE = [
  route(PATHS.training, pages.trainingPlan),
  route(`${PATHS.training}/workouts/:id(\\d+)`, pages.workoutDay),
  route(`${PATHS.training}/workouts/:id(\\d+)/exercises/:itemId(\\d+)`, pages.exerciseDetail),
  route(PATHS.nutrition, pages.nutrition),
  route(PATHS.clientFoods, pages.clientFoods),
  route(`${PATHS.clientFoods}/:id(\\d+)`, pages.clientFood),
  route(PATHS.foodDiary, pages.foodDiary),
  route(PATHS.shoppingList, pages.shoppingList),
  route(PATHS.progress, pages.progress),
  route(PATHS.badges, pages.badges),
  route(PATHS.notes, pages.notes),
  ...PROFILE,
];

// Ids only match digits, so "new" never opens a detail page.
const CATALOG = [
  route(PATHS.catalog, pages.catalog),
  route(`${PATHS.catalog}/workouts/new`, pages.workoutForm),
  route(`${PATHS.catalog}/workouts/:id(\\d+)/edit`, pages.workoutForm),
  route(`${PATHS.catalog}/workouts/:id(\\d+)`, pages.workoutDetail),
  route(`${PATHS.catalog}/exercises/new`, pages.exerciseForm),
  route(`${PATHS.catalog}/exercises/:id(\\d+)/edit`, pages.exerciseForm),
  route(`${PATHS.catalog}/exercises/:id(\\d+)`, pages.exerciseStaff),
  route(`${PATHS.catalog}/plans/new`, pages.planForm),
  route(`${PATHS.catalog}/plans/:id(\\d+)/edit`, pages.planForm),
  route(`${PATHS.catalog}/plans/:id(\\d+)`, pages.planDetail),
];

const MEAL_PLANS = [
  route(PATHS.mealPlans, pages.mealPlans),
  route(`${PATHS.mealPlans}/new`, pages.mealPlanForm),
  route(`${PATHS.mealPlans}/:id(\\d+)/edit`, pages.mealPlanForm),
  route(`${PATHS.mealPlans}/:id(\\d+)`, pages.mealPlanDetail),
  route(`${PATHS.mealPlans}/:id(\\d+)/menu`, pages.menuEditor),
  // Food library (phase 9): "foods" never matches the digit-only plan ids above.
  route(PATHS.foods, pages.staffFoods),
  route(`${PATHS.foods}/new`, pages.foodForm),
  route(`${PATHS.foods}/:id(\\d+)/edit`, pages.foodForm),
  route(`${PATHS.foods}/:id(\\d+)`, pages.staffFood),
];

const STAFF_COMMON = [
  route(PATHS.users, pages.users),
  route(`${PATHS.users}/:id(\\d+)`, pages.userDetail),
  route(PATHS.adherence, pages.adherence),
  route(PATHS.assignments, pages.assignments),
  route(`${PATHS.assignments}/:userId(\\d+)`, pages.assignmentDetail),
  ...PROFILE,
];

const ADMIN_ONLY = [
  route(PATHS.statistics, pages.statistics),
  route(`${PATHS.users}/new`, pages.userCreate),
  route(`${PATHS.users}/:id(\\d+)/edit`, pages.userEdit),
];

/** Pages registered under /app for each role/status, with a key that names the set. */
export const routesFor = (user: Me): { key: string; routes: AppRoute[] } => {
  switch (user.role) {
    case 'client':
      return isActiveClient(user)
        ? { key: 'client-active', routes: CLIENT_ACTIVE }
        : { key: 'client-pending', routes: CLIENT_PENDING };
    case 'trainer':
      return { key: 'trainer', routes: [...CATALOG, ...STAFF_COMMON] };
    case 'nutritionist':
      return { key: 'nutritionist', routes: [...MEAL_PLANS, ...STAFF_COMMON] };
    case 'admin':
      return { key: 'admin', routes: [...ADMIN_ONLY, ...CATALOG, ...MEAL_PLANS, ...STAFF_COMMON] };
  }
};
