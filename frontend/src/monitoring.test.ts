import type { ErrorEvent } from '@sentry/browser';

import { scrubBreadcrumb, scrubEvent, scrubUrl } from './monitoring';

describe('error monitoring privacy', () => {
  it('hides the tokens of password reset links', () => {
    expect(scrubUrl('https://app.example.com/reset-password?uid=MQ&token=abc-123')).toBe(
      'https://app.example.com/reset-password?uid=[Filtered]&token=[Filtered]',
    );
    expect(scrubUrl('/app/training')).toBe('/app/training');
  });

  it('drops user data, bodies and cookies from events', () => {
    const event = {
      type: undefined,
      user: { email: 'ana@example.com' },
      request: {
        url: '/reset-password?token=abc',
        data: '{"weight_kg": 80}',
        cookies: { a: 'b' },
        query_string: 'token=abc',
      },
    } as unknown as ErrorEvent;

    expect(scrubEvent(event)).toEqual({
      type: undefined,
      request: { url: '/reset-password?token=[Filtered]' },
    });
  });

  it('cleans navigation and request breadcrumbs', () => {
    expect(
      scrubBreadcrumb({
        category: 'navigation',
        data: { from: '/login', to: '/reset-password?token=x' },
      }),
    ).toEqual({
      category: 'navigation',
      data: { from: '/login', to: '/reset-password?token=[Filtered]' },
    });
  });
});
