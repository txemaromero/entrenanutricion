/**
 * Data shown in the privacy policy. Set them at build time for each deployment; the version must
 * match PRIVACY_POLICY_VERSION of the API and the retention days its ACCOUNT_RETENTION_DAYS and
 * BACKUP_RETENTION_DAYS (README → Variables de entorno).
 */
export const PRIVACY = {
  version: import.meta.env.VITE_PRIVACY_POLICY_VERSION ?? '2026-11',
  controller: import.meta.env.VITE_PRIVACY_CONTROLLER ?? '',
  contact: import.meta.env.VITE_PRIVACY_CONTACT ?? '',
  accountRetentionDays: Number(import.meta.env.VITE_ACCOUNT_RETENTION_DAYS ?? 365),
  backupRetentionDays: Number(import.meta.env.VITE_BACKUP_RETENTION_DAYS ?? 14),
};

/** Sections of the policy, in order (texts in `privacy.sections.<key>`). */
export const PRIVACY_SECTIONS = [
  'controller',
  'data',
  'purposes',
  'legalBasis',
  'recipients',
  'retention',
  'rights',
  'security',
] as const;
