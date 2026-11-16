import type { BADGE_CODES } from '../utils/badges';
import type { FOOD_CATEGORIES, NutrientKey } from '../utils/foods';

/** Domain types as seen by components (camelCase). Mirror the backend serializers. */

export type Role = 'client' | 'admin' | 'trainer' | 'nutritionist';
export type UserStatus = 'pending_onboarding' | 'pending_assignment' | 'active' | 'inactive';
export type Gender = 'M' | 'F' | 'O';
export type Goal = 'lose_weight' | 'gain_muscle' | 'maintain';
export type ActivityLevel = 'sedentary' | 'light' | 'moderate' | 'intense';
export type DailyTrainingTime = 'lt_1h' | '1_2h' | 'gt_2h';
export type ExerciseType = 'cardio' | 'strength' | 'flexibility' | 'circuit' | 'other';
export type Equipment = 'full_gym' | 'free_weights' | 'cardio_machines' | 'no_equipment' | 'other';
export type TrainingPreference = 'home' | 'gym' | 'outdoor' | 'group_classes' | 'other';
export type DietType = 'omnivore' | 'vegetarian' | 'vegan' | 'low_carb' | 'high_protein' | 'other';
export type FoodRestriction = 'allergies' | 'intolerances' | 'dietary_preferences' | 'none';
export type MacroSelfAssessment = 'low_protein' | 'low_carbs' | 'low_fats' | 'balanced' | 'unknown';
export type MedicalCondition = 'diabetes' | 'hypertension' | 'joint_problems' | 'other' | 'none';
export type Supplement = 'protein' | 'multivitamin' | 'omega3' | 'other' | 'none';
export type Difficulty = 'beginner' | 'intermediate' | 'advanced';
export type MealPlanCategory = 'weight_loss' | 'muscle_gain' | 'maintenance';
export type FoodCategory = (typeof FOOD_CATEGORIES)[number];
export type DietLabel =
  | 'balanced'
  | 'high_protein'
  | 'low_carb'
  | 'low_fat'
  | 'mediterranean'
  | 'vegetarian'
  | 'vegan'
  | 'keto';
export type MediaKind = 'image' | 'video';
export type WorkoutStatus = 'locked' | 'available' | 'completed';
export type Meal = 'breakfast' | 'lunch' | 'dinner' | 'snacks';

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** The refresh token is never in a body: it is an httpOnly cookie. */
export interface AccessToken {
  access: string;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface MeDetails {
  heightCm: number;
  initialWeightKg: number;
  currentWeightKg: number | null;
  targetWeightKg: number;
  targetWeightChangeKg: number;
  goal: Goal;
  physicalActivityLevel: ActivityLevel;
  weeklyTrainingDays: number;
  dailyTrainingTime: DailyTrainingTime;
}

export type AppLanguage = 'es' | 'en' | 'ca';

export interface Me {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  birthDate: string | null;
  age: number | null;
  gender: Gender | '';
  role: Role;
  status: UserStatus;
  profilePhotoUrl: string | null;
  onboardingCompleted: boolean;
  hasTrainingPlan: boolean;
  hasNutritionPlan: boolean;
  /** The current privacy policy (or the health data consent) has not been accepted yet. */
  consentRequired: boolean;
  /** Self-registered accounts confirm the address with the emailed link. */
  emailVerified: boolean;
  /** Language of the app stored in the account (the emails are written in it). */
  language: AppLanguage;
  details: MeDetails | null;
  dateJoined: string;
}

/** Training time ("HH:MM") and opt-in email reminders on training days. */
export interface Reminders {
  enabled: boolean;
  trainingTime: string;
  /** False while the default time of the platform is used. */
  customTime: boolean;
  defaultTrainingTime: string;
}

export interface AuthResponse extends AccessToken {
  user: Me;
}

export interface RegisterInput {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  birthDate: string;
  gender: Gender;
  termsAccepted: boolean;
  healthDataConsent: boolean;
}

export interface ConsentInput {
  privacyPolicy: boolean;
  healthData: boolean;
}

export interface PasswordResetInput {
  uid: string;
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ProfileUpdateInput {
  language?: AppLanguage;
  firstName?: string;
  lastName?: string;
  currentWeightKg?: number;
  goal?: Goal;
  physicalActivityLevel?: ActivityLevel;
  weeklyTrainingDays?: number;
}

export interface PasswordChangeInput {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

export interface DietPreferences {
  dietType: DietType;
  foodRestrictions: FoodRestriction[];
  customFoodRestrictions: string;
  mealsPerDay: number;
  macronutrientIntakeSelfAssessment: MacroSelfAssessment;
}

export interface HealthInfo {
  medicalConditions: MedicalCondition[];
  customMedicalCondition: string;
  supplements: Supplement[];
}

export interface Onboarding {
  heightCm: number;
  initialWeightKg: number;
  goal: Goal;
  targetWeightChangeKg: number;
  targetWeightKg?: number;
  weeklyTrainingDays: number;
  dailyTrainingTime: DailyTrainingTime;
  physicalActivityLevel: ActivityLevel;
  usualExerciseTypes: ExerciseType[];
  availableEquipment: Equipment[];
  trainingPreference: TrainingPreference;
  preferencesText: string;
  /** Read only: picked from the training plan (empty = default calendar). */
  trainingDays?: number[];
  diet: DietPreferences;
  health: HealthInfo;
}

export interface TrainingDays {
  days: number[];
  custom: boolean;
  weeklyTrainingDays: number;
}

// --- Training catalog -------------------------------------------------------------------------

export interface MuscleGroup {
  id: number;
  name: string;
  slug: string;
}

export interface ExerciseMedia {
  id: number;
  url: string;
  kind: MediaKind;
  caption: string;
  order: number;
}

export interface ExerciseSummary {
  id: number;
  name: string;
  description?: string;
  muscleGroups: MuscleGroup[];
  thumbnailUrl: string | null;
  isActive: boolean;
}

/** Texts of a catalog item that can be translated (exercise steps as a list). */
export type TranslatedTextKey =
  'name' | 'description' | 'technique' | 'commonMistakes' | 'benefits';
export type TranslatedTexts = Partial<Record<TranslatedTextKey, string>> & { steps?: string[] };

/** Every language of a catalog item: `es` is the base text (the normal fields), `en`/`ca` optional. */
export interface CatalogTranslations {
  es: TranslatedTexts;
  en?: TranslatedTexts;
  ca?: TranslatedTexts;
}

/** A language as the forms edit it (a step left untranslated is empty). */
export type TranslatedTextsInput = Omit<TranslatedTexts, 'steps'> & {
  steps?: (string | undefined)[];
};

/** What the staff send: the translations (the Spanish text goes in the normal fields). */
export interface TranslationsInput {
  en: TranslatedTextsInput;
  ca: TranslatedTextsInput;
}

export interface Exercise extends ExerciseSummary {
  description: string;
  technique: string;
  commonMistakes: string;
  benefits: string;
  steps: string[];
  media: ExerciseMedia[];
  translations: CatalogTranslations;
}

export interface ExerciseInput {
  name: string;
  description: string;
  technique: string;
  commonMistakes: string;
  benefits: string;
  muscleGroupIds: number[];
  steps: string[];
  translations?: TranslationsInput;
}

export interface WorkoutTotals {
  estimatedDurationMinutes: number;
  totalSets: number;
  totalReps: number;
  exerciseCount: number;
}

export interface WorkoutItem {
  id: number;
  order: number;
  sets: number;
  reps: number;
  restSeconds: number;
  exercise: ExerciseSummary;
}

export interface WorkoutSummary extends WorkoutTotals {
  id: number;
  name: string;
  description: string;
  mediaUrl: string | null;
  mediaKind: MediaKind | null;
  durationMinutes?: number | null;
}

export interface Workout extends WorkoutSummary {
  durationMinutes: number | null;
  exercises: WorkoutItem[];
  translations: CatalogTranslations;
}

export interface WorkoutInput {
  translations?: TranslationsInput;
  name: string;
  description: string;
  durationMinutes: number | null;
  exercises: { id?: number; exerciseId: number; sets: number; reps: number; restSeconds: number }[];
}

export interface TrainingPlanSummary {
  id: number;
  name: string;
  description: string;
  mediaUrl: string | null;
  mediaKind: MediaKind | null;
  goal: Goal;
  difficulty: Difficulty;
  equipment: Equipment;
  durationWeeks: number;
  isActive: boolean;
  workoutCount: number;
}

export interface TrainingPlan extends Omit<TrainingPlanSummary, 'workoutCount'> {
  workouts: { id: number; order: number; workout: WorkoutSummary }[];
  sessionsPerWeek: number;
  translations: CatalogTranslations;
}

export interface TrainingPlanInput {
  translations?: TranslationsInput;
  name: string;
  description: string;
  goal: Goal;
  difficulty: Difficulty;
  equipment: Equipment;
  durationWeeks: number;
  workouts: { id?: number; workoutId: number }[];
}

// --- Client training --------------------------------------------------------------------------

export interface WorkoutRef {
  id: number;
  name: string;
  description: string;
  mediaUrl: string | null;
  mediaKind: MediaKind | null;
}

export interface PlanWorkout {
  id: number;
  order: number;
  status: WorkoutStatus;
  completedAt: string | null;
  scheduledDate: string | null;
  workout: WorkoutRef;
  summary: WorkoutTotals;
}

export interface MyTrainingPlan {
  id: number;
  cycle: number;
  progress: number;
  dateStarted: string;
  weeklyTrainingDays: number | null;
  /** Weekdays the workouts are scheduled on (Monday = 0). */
  trainingDays: number[];
  customTrainingDays: boolean;
  plan: WorkoutRef & {
    goal: Goal;
    difficulty: Difficulty;
    equipment: Equipment;
    durationWeeks: number;
  };
  workouts: PlanWorkout[];
  nextWorkoutId: number | null;
}

export interface DayProgress {
  completed: number;
  total: number;
  percent: number;
}

/** One set done: repetitions and, for weighted exercises, the load. */
export interface SetEntry {
  reps: number;
  weightKg: number | null;
}

export interface DayExercise {
  id: number;
  order: number;
  /** Planned sets and repetitions per set. */
  sets: number;
  reps: number;
  restSeconds: number;
  completed: boolean;
  /** Sets logged so far in this workout. */
  loggedSets: SetEntry[];
  /** Sets of the last session of this exercise (null if never done). */
  lastSets: SetEntry[] | null;
  exercise: ExerciseSummary;
}

export interface NewRecord {
  exerciseId: number;
  exerciseName: string;
  weightKg: number;
  reps: number;
}

export interface PersonalRecord {
  exercise: { id: number; name: string };
  bestWeightKg: number;
  bestWeightReps: number;
  bestWeightDate: string;
  estimatedOneRmKg: number;
}

export interface ExerciseHistory {
  record: PersonalRecord | null;
  entries: { date: string; sets: SetEntry[]; maxWeightKg: number | null; volumeKg: number }[];
}

export interface WorkoutDay extends PlanWorkout {
  progress: DayProgress;
  exercises: DayExercise[];
}

export interface Motivation {
  keys: string[];
  params: Record<string, number>;
}

export interface WorkoutSession {
  id: number;
  workoutId: number | null;
  workoutName: string;
  cycle: number;
  completedAt: string;
  totalSets: number;
  totalReps: number;
  durationMinutes: number;
}

export interface CompleteWorkoutResult {
  session: WorkoutSession;
  cycleCompleted: boolean;
  cycle: number;
  planProgress: number;
  nextWorkoutId: number | null;
  motivation: Motivation;
  /** Badges awarded by this workout. */
  newBadges: BadgeCode[];
  /** Exercises whose heaviest set beats the previous best. */
  newRecords: NewRecord[];
}

// --- Nutrition ----------------------------------------------------------------------------------

export type MealDistribution = Record<Meal, number>;

export interface MacroValue {
  grams: number;
  kcal: number;
  pct: number;
}

export interface Macros {
  proteins: MacroValue;
  carbs: MacroValue;
  fats: MacroValue;
  totalKcal: number;
}

/** Food library entry; every value is per 100 g (optional nutrients may be null). */
export interface Food extends Record<NutrientKey, number | null> {
  id: number;
  name: string;
  category: FoodCategory;
  calories: number;
  proteinsG: number;
  carbsG: number;
  fatsG: number;
  macros: Macros;
  translations: CatalogTranslations;
  createdAt: string;
  updatedAt: string;
}

export type FoodInput = Omit<Food, 'id' | 'macros' | 'createdAt' | 'updatedAt' | 'translations'> & {
  translations?: TranslationsInput;
};

export interface MealRow {
  meal: Meal;
  pct: number;
  kcal: number;
  proteinsG: number;
  carbsG: number;
  fatsG: number;
}

export interface MealPlanSummary {
  id: number;
  name: string;
  category: MealPlanCategory;
  dietLabel: DietLabel;
  calories: number;
  proteinsG: number;
  carbsG: number;
  fatsG: number;
  isActive: boolean;
}

export interface MealPlan extends MealPlanSummary {
  mealDistribution: MealDistribution;
  description: string;
  macros: Macros;
  meals: MealRow[];
  translations: CatalogTranslations;
}

export interface MealPlanInput {
  translations?: TranslationsInput;
  name: string;
  category: MealPlanCategory;
  dietLabel: DietLabel;
  calories: number;
  proteinsG: number;
  carbsG: number;
  fatsG: number;
  mealDistribution: MealDistribution;
  description: string;
}

export interface MyNutritionPlan {
  id: number;
  name: string;
  category: MealPlanCategory;
  dietLabel: DietLabel;
  description: string;
  calories: number;
  dateAssigned: string;
  macros: Macros;
  meals: MealRow[];
}

// --- Progress -----------------------------------------------------------------------------------

export interface Dashboard {
  month: string;
  completedDays: string[];
  scheduledDays: string[];
  nextWorkout: {
    id: number;
    workoutName: string;
    scheduledDate: string;
    targetDatetime: string;
  } | null;
  planName: string;
  planProgress: number;
  cycle: number;
  totalSessions: number;
  /** This week, Monday to Sunday. */
  week: WeekDay[];
  /** Weeks in a row, within the current plan, with every scheduled session done. */
  streakWeeks: number;
  motivation: Motivation;
}

export interface WeekDay {
  date: string;
  scheduled: boolean;
  completed: boolean;
}

/** One week (Monday to Sunday) of `/me/progress/stats`. */
export interface WeekStats {
  start: string;
  sessions: number;
  minutes: number;
  /** Repetitions × kilos of the sets with load. */
  volumeKg: number;
}

export interface MuscleGroupStats {
  slug: string;
  name: string;
  sets: number;
}

export interface TrainingStats {
  /** The last 12 weeks, oldest first. */
  weeks: WeekStats[];
  /** Sets per muscle group in the last 28 days, most worked first. */
  muscleGroups: MuscleGroupStats[];
}

export interface WeightPoint {
  id: number;
  date: string;
  weightKg: number;
}

export interface WeightSummary {
  goal: Goal;
  initialWeightKg: number;
  targetWeightKg: number;
  currentWeightKg: number | null;
  records: WeightPoint[];
  /** Only in the answer to a new weight: badges it awarded. */
  newBadges?: BadgeCode[];
}

// --- Badges (gamification) --------------------------------------------------------------------

export type BadgeCode = (typeof BADGE_CODES)[number];

export interface Badge {
  code: BadgeCode;
  earned: boolean;
  awardedAt: string | null;
  current: number;
  target: number;
}

export interface BadgesOverview {
  earnedCount: number;
  total: number;
  newBadges: BadgeCode[];
  badges: Badge[];
}

// --- Users & assignments -----------------------------------------------------------------------

export interface PlanRef {
  id: number;
  name: string;
}

export interface UserSummary {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  role: Role;
  status: UserStatus;
  profilePhotoUrl: string | null;
  trainingPlan: PlanRef | null;
  nutritionPlan: PlanRef | null;
  dateJoined: string;
}

/** Note of the thread between a client and the professional team (newest first in lists). */
export interface Note {
  id: number;
  body: string;
  authorName: string;
  authorRole: Role;
  fromClient: boolean;
  createdAt: string;
  /** When the other side read it. */
  readAt: string | null;
}

export interface NotesInboxEntry {
  client: Pick<UserSummary, 'id' | 'fullName' | 'email' | 'profilePhotoUrl'>;
  unread: number;
  lastNoteAt: string;
  lastNote: string;
}

export type AdherenceStatus = 'inactive' | 'at_risk' | 'on_track';

/** Sessions done against the scheduled ones in the last 28 days (staff). */
export interface AdherenceRow {
  user: Pick<UserSummary, 'id' | 'fullName' | 'email' | 'profilePhotoUrl'>;
  planName: string;
  planStarted: string;
  sessions: number;
  scheduled: number;
  /** Null while nothing has been scheduled yet (new plan). */
  adherencePercent: number | null;
  lastSessionDate: string | null;
  daysSinceLastSession: number | null;
  currentWeightKg: number | null;
  weightChangeKg: number | null;
  status: AdherenceStatus;
}

export interface ClientAdherence extends AdherenceRow {
  weeks: { start: string; end: string; sessions: number; scheduled: number }[];
}

export interface AdherenceList extends Paginated<AdherenceRow> {
  /** Clients per status, worst first (the status filter does not change them). */
  counts: { status: AdherenceStatus; count: number }[];
  /** Clients per band of 20 points (low–high %), before the status filter. */
  distribution: { low: number; high: number; count: number }[];
  /** Mean adherence of the clients with something scheduled (null if none). */
  averagePercent: number | null;
}

export interface UserDetail extends UserSummary {
  birthDate: string | null;
  age: number | null;
  gender: Gender | '';
  details: MeDetails | null;
  onboarding: Onboarding | null;
  weightRecords: WeightPoint[];
  trainingAssignment: {
    id: number;
    plan: PlanRef;
    cycle: number;
    progress: number;
    dateStarted: string;
  } | null;
  nutritionAssignment: { id: number; plan: PlanRef; dateAssigned: string } | null;
}

export interface UserCreateInput {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  gender: Gender;
  role: Role;
  birthDate: string;
}

export interface UserUpdateInput extends ProfileUpdateInput {
  role?: Role;
}

export type MissingPlan = 'training' | 'nutrition';

export interface PendingUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  fullName: string;
  profilePhotoUrl: string | null;
  goal: Goal;
  weeklyTrainingDays: number;
  dateJoined: string;
  missing: MissingPlan[];
}

// --- Statistics ---------------------------------------------------------------------------------

export interface StatisticsSummary {
  usersByRole: Record<Role, number>;
  activeClients: number;
  pendingAssignment: number;
  pendingOnboarding: number;
  sessionsThisMonth: number;
  /** Same days of the previous month (1st to today's day). */
  sessionsPreviousPeriod: number;
  newClientsThisMonth: number;
  newClientsPreviousPeriod: number;
  /** Active clients per goal. */
  clientsByGoal: { loseWeight: number; gainMuscle: number; maintain: number };
}

export interface PlanPopularityRow {
  planId: number;
  name: string;
  /** Clients with the plan assigned right now. */
  count: number;
}

export interface PopularityRow {
  exerciseId: number;
  name: string;
  count: number;
}

export interface GrowthRow {
  month: number;
  count: number;
}

// --- Menus, shopping list and food diary (phase 13) --------------------------------------------

export interface FoodRef {
  id: number;
  name: string;
  category: FoodCategory;
}

/** Calories and macros of a portion, a meal or a day. */
export interface Nutrients {
  calories: number;
  proteinsG: number;
  carbsG: number;
  fatsG: number;
}

export interface MenuItem extends Nutrients {
  id: number;
  food: FoodRef;
  grams: number;
}

export interface MenuMeal {
  meal: Meal;
  items: MenuItem[];
  totals: Nutrients;
  /** The plan's targets for this meal. */
  target: Nutrients;
}

/** Sample day menu of a nutrition plan. */
export interface Menu {
  hasMenu: boolean;
  meals: MenuMeal[];
  totals: Nutrients;
  target: Nutrients;
  caloriesDeviationPct: number | null;
  withinTolerance: boolean;
}

export interface MenuItemInput {
  meal: Meal;
  foodId: number;
  grams: number;
}

export interface ShoppingList {
  days: number;
  hasMenu: boolean;
  items: { food: FoodRef; grams: number }[];
}

/** A food the client ate; the values were copied when it was logged. */
export interface FoodLogEntry extends Nutrients {
  id: number;
  date: string;
  meal: Meal;
  foodId: number | null;
  foodName: string;
  grams: number;
}

export interface DiaryDay {
  date: string;
  /** Daily targets of the current plan (null without a plan). */
  target: Nutrients | null;
  totals: Nutrients;
  meals: {
    meal: Meal;
    targetCalories: number | null;
    totals: Nutrients;
    entries: FoodLogEntry[];
  }[];
}

export interface DiarySummary {
  targetCalories: number | null;
  daysLogged: number;
  averageCalories: number | null;
  /** Oldest first, today last. */
  days: (Nutrients & { date: string; entries: number })[];
}
