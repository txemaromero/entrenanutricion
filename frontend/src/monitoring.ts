import type { Breadcrumb, ErrorEvent } from '@sentry/browser';

/**
 * Error monitoring with Sentry, loaded only in production builds with VITE_SENTRY_DSN. Nothing
 * personal is sent: no user data, no request bodies and no tokens in URLs (password reset links).
 */
export const scrubUrl = (url: string): string =>
  url.replace(/([?&](?:token|uid)=)[^&#]*/g, '$1[Filtered]');

export const scrubEvent = (event: ErrorEvent): ErrorEvent => {
  delete event.user;
  if (event.request) {
    if (event.request.url) event.request.url = scrubUrl(event.request.url);
    delete event.request.cookies;
    delete event.request.data;
    delete event.request.query_string;
  }
  return event;
};

export const scrubBreadcrumb = (breadcrumb: Breadcrumb): Breadcrumb => {
  const data = breadcrumb.data;
  if (data) {
    for (const key of ['url', 'from', 'to']) {
      if (typeof data[key] === 'string') data[key] = scrubUrl(data[key] as string);
    }
  }
  return breadcrumb;
};

export const initMonitoring = async (dsn: string) => {
  const Sentry = await import('@sentry/browser');
  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT ?? 'production',
    release: import.meta.env.VITE_SENTRY_RELEASE,
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpHeaders: false,
      httpBodies: [],
      urlQueryParams: false,
    },
    tracesSampleRate: 0,
    beforeSend: scrubEvent,
    beforeBreadcrumb: scrubBreadcrumb,
  });
};
