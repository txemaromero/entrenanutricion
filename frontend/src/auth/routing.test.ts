import type { Me, Role, UserStatus } from '../api/types';
import { allowedSections, homePath, isPathAllowed, tabsFor } from './routing';

const user = (role: Role, status: UserStatus = 'active'): Me => ({
  id: 1,
  email: 'x@example.com',
  firstName: 'Ana',
  lastName: 'Gil',
  fullName: 'Ana Gil',
  birthDate: '1990-01-01',
  age: 36,
  gender: 'F',
  role,
  status,
  profilePhotoUrl: null,
  onboardingCompleted: status !== 'pending_onboarding',
  hasTrainingPlan: status === 'active',
  hasNutritionPlan: status === 'active',
  consentRequired: false,
  emailVerified: true,
  language: 'es',
  details: null,
  dateJoined: '2026-01-01T00:00:00Z',
});

const keys = (u: Me) => tabsFor(u).map((tab) => tab.key);

describe('navigation rules', () => {
  it('home path depends on role and status', () => {
    expect(homePath(null)).toBe('/welcome');
    expect(homePath(user('client', 'pending_onboarding'))).toBe('/onboarding');
    expect(homePath(user('client', 'pending_assignment'))).toBe('/app/status');
    expect(homePath(user('client', 'active'))).toBe('/app/training');
    expect(homePath(user('trainer'))).toBe('/app/catalog');
    expect(homePath(user('nutritionist'))).toBe('/app/meal-plans');
    expect(homePath(user('admin'))).toBe('/app/catalog');
  });

  it('tabs per role', () => {
    expect(keys(user('client', 'pending_assignment'))).toEqual(['status', 'profile']);
    expect(keys(user('client'))).toEqual(['training', 'nutrition', 'progress', 'profile']);
    expect(keys(user('trainer'))).toEqual(['catalog', 'users', 'assignments', 'profile']);
    expect(keys(user('nutritionist'))).toEqual(['mealPlans', 'users', 'assignments', 'profile']);
    expect(keys(user('admin'))).toEqual([
      'catalog',
      'mealPlans',
      'users',
      'assignments',
      'statistics',
    ]);
  });

  it('no tab path is a prefix of another (only one tab can be active)', () => {
    for (const role of ['client', 'trainer', 'nutritionist', 'admin'] as Role[]) {
      const paths = tabsFor(user(role)).map((tab) => tab.path);
      paths.forEach((path, i) =>
        paths.forEach((other, j) => {
          if (i !== j) expect(other.startsWith(`${path}/`) || other === path).toBe(false);
        }),
      );
    }
  });

  it('admin reaches the profile without a tab', () => {
    expect(allowedSections(user('admin'))).toContain('/app/profile');
  });

  it('guards sections by role and status', () => {
    expect(isPathAllowed(user('client', 'pending_assignment'), '/app/training')).toBe(false);
    expect(isPathAllowed(user('client'), '/app/training/workouts/3')).toBe(true);
    expect(isPathAllowed(user('client'), '/app/users')).toBe(false);
    expect(isPathAllowed(user('trainer'), '/app/meal-plans')).toBe(false);
    expect(isPathAllowed(user('trainer'), '/app/statistics')).toBe(false);
    expect(isPathAllowed(user('nutritionist'), '/app/catalog')).toBe(false);
    expect(isPathAllowed(user('admin'), '/app/statistics')).toBe(true);
    expect(isPathAllowed(user('admin'), '/app/trainingx')).toBe(false);
  });
});
