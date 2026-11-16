/**
 * Security headers of the production app. The same values are written in
 * docker/security-headers.conf (nginx) and render.yaml (static site); tests/security-headers.test.ts
 * keeps the three in sync, and `vite preview` serves them so the build can be tested with them.
 *
 * - Scripts: only the app's own files (the build has no inline scripts and no eval).
 * - Styles: Ionic injects inline styles, hence 'unsafe-inline' for styles only.
 * - Images and videos: signed URLs of Google Cloud Storage.
 * - Requests: the API on the same origin (Vite proxy, nginx or the Render rewrite) and Sentry.
 */
export const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob: https://storage.googleapis.com",
  "media-src 'self' blob: https://storage.googleapis.com",
  "font-src 'self' data:",
  "connect-src 'self' https://*.ingest.sentry.io https://*.ingest.de.sentry.io",
  "worker-src 'self'",
  "manifest-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join('; ');

export const SECURITY_HEADERS: Record<string, string> = {
  'Content-Security-Policy': CONTENT_SECURITY_POLICY,
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'same-origin',
  'X-Frame-Options': 'DENY',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
};

/**
 * HTTPS only (browsers ignore it over plain HTTP): the Render static site sends it, like the API
 * (Django's SECURE_HSTS_SECONDS). Not in SECURITY_HEADERS because nginx (docker-compose.prod.yml)
 * and `vite preview` serve plain HTTP on this machine.
 */
export const STRICT_TRANSPORT_SECURITY = 'max-age=31536000; includeSubDomains';
