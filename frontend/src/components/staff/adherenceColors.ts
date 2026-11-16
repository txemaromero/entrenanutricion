import type { AdherenceStatus } from '../../api/types';

/** Status colours (always with their name next to them): the same as the status chips. */
export const ADHERENCE_COLOR_VARS: Record<AdherenceStatus, string> = {
  inactive: '--ion-color-danger',
  at_risk: '--ion-color-warning',
  on_track: '--ion-color-success',
};
