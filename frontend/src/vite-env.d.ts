/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_PRIVACY_POLICY_VERSION?: string;
  readonly VITE_PRIVACY_CONTROLLER?: string;
  readonly VITE_PRIVACY_CONTACT?: string;
  readonly VITE_ACCOUNT_RETENTION_DAYS?: string;
  readonly VITE_BACKUP_RETENTION_DAYS?: string;
  readonly VITE_SENTRY_ENVIRONMENT?: string;
  readonly VITE_SENTRY_RELEASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
