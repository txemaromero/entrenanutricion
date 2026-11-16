import type { TFunction } from 'i18next';

import type { BadgeCode } from '../api/types';

/** Same order as the backend (`apps.progress.models.BadgeCode`). */
export const BADGE_CODES = [
  'first_workout',
  'workouts_10',
  'workouts_50',
  'workouts_100',
  'perfect_week',
  'first_cycle',
  'weight_logs_10',
  'goal_reached',
] as const;

/** "New badge: Perfect week!" for the badges a request has just awarded ('' when none). */
export const newBadgesText = (t: TFunction, codes: BadgeCode[] | undefined): string =>
  codes?.length
    ? t('badges.newBadge', {
        count: codes.length,
        names: codes.map((code) => t(`badges.items.${code}.name`)).join(', '),
      })
    : '';
