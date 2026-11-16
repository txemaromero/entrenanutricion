import type { Me } from '../api/types';

/** Navigation rules per role and status. Pure functions, unit tested. */

export const PATHS = {
  welcome: '/welcome',
  login: '/login',
  register: '/register',
  forgotPassword: '/forgot-password',
  resetPassword: '/reset-password',
  privacy: '/privacy',
  verifyEmail: '/verify-email',
  onboarding: '/onboarding',
  status: '/app/status',
  training: '/app/training',
  nutrition: '/app/nutrition',
  progress: '/app/progress',
  badges: '/app/progress/badges',
  profile: '/app/profile',
  notes: '/app/profile/notes',
  catalog: '/app/catalog',
  mealPlans: '/app/meal-plans',
  foods: '/app/meal-plans/foods',
  clientFoods: '/app/nutrition/foods',
  foodDiary: '/app/nutrition/diary',
  shoppingList: '/app/nutrition/shopping-list',
  users: '/app/users',
  adherence: '/app/users/adherence',
  assignments: '/app/assignments',
  statistics: '/app/statistics',
} as const;

export type TabKey =
  | 'status'
  | 'training'
  | 'nutrition'
  | 'progress'
  | 'profile'
  | 'catalog'
  | 'mealPlans'
  | 'users'
  | 'assignments'
  | 'statistics';

export interface TabDef {
  key: TabKey;
  path: string;
  labelKey: string;
}

const tab = (key: TabKey): TabDef => ({ key, path: PATHS[key], labelKey: `tabs.${key}` });

export const isActiveClient = (user: Me): boolean =>
  user.role === 'client' && user.status === 'active';

export const tabsFor = (user: Me): TabDef[] => {
  switch (user.role) {
    case 'client':
      return isActiveClient(user)
        ? [tab('training'), tab('nutrition'), tab('progress'), tab('profile')]
        : [tab('status'), tab('profile')];
    case 'trainer':
      return [tab('catalog'), tab('users'), tab('assignments'), tab('profile')];
    case 'nutritionist':
      return [tab('mealPlans'), tab('users'), tab('assignments'), tab('profile')];
    case 'admin':
      // Admin profile is reached from the avatar in the top bar (5 tabs only).
      return [
        tab('catalog'),
        tab('mealPlans'),
        tab('users'),
        tab('assignments'),
        tab('statistics'),
      ];
  }
};

export const homePath = (user: Me | null): string => {
  if (!user) return PATHS.welcome;
  if (user.role === 'client' && user.status === 'pending_onboarding') return PATHS.onboarding;
  return tabsFor(user)[0].path;
};

/** Top-level sections the user may open: every tab plus the profile. */
export const allowedSections = (user: Me): string[] => {
  const sections = tabsFor(user).map((item) => item.path);
  return sections.includes(PATHS.profile) ? sections : [...sections, PATHS.profile];
};

export const isPathAllowed = (user: Me, pathname: string): boolean =>
  allowedSections(user).some(
    (section) => pathname === section || pathname.startsWith(`${section}/`),
  );
