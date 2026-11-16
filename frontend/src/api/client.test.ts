import axios, { AxiosError, type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios';

import { api, refreshAccessToken, setApiLanguage, setSessionExpiredHandler } from './client';
import { ApiError } from './errors';
import { tokens } from './tokens';

const respond = (config: InternalAxiosRequestConfig, status: number, data: unknown) => {
  const response = { data, status, statusText: '', headers: {}, config };
  if (status >= 400) {
    return Promise.reject(new AxiosError('error', String(status), config, null, response));
  }
  return Promise.resolve(response);
};

describe('api client', () => {
  let adapter: ReturnType<typeof vi.fn<AxiosAdapter>>;

  beforeEach(() => {
    tokens.clear();
    adapter = vi.fn<AxiosAdapter>();
    api.defaults.adapter = adapter;
  });

  afterEach(() => vi.restoreAllMocks());

  it('sends snake_case bodies, auth and language headers and returns camelCase', async () => {
    tokens.setAccess('token-1');
    setApiLanguage('ca');
    adapter.mockImplementation((config) => respond(config, 200, { current_weight_kg: 70 }));

    const { data } = await api.patch(
      '/me/profile',
      { currentWeightKg: 70 },
      { params: { roleFilter: 'x' } },
    );

    const config = adapter.mock.calls[0][0];
    expect(JSON.parse(config.data as string)).toEqual({ current_weight_kg: 70 });
    expect(config.params).toEqual({ role_filter: 'x' });
    expect(config.headers.Authorization).toBe('Bearer token-1');
    expect(config.headers['Accept-Language']).toBe('ca');
    expect(config.headers['X-Requested-With']).toBe('entrenanutricion');
    expect(config.withCredentials).toBe(true);
    expect(data).toEqual({ currentWeightKg: 70 });
  });

  it('turns error bodies into ApiError with camelCase fields', async () => {
    adapter.mockImplementation((config) =>
      respond(config, 400, {
        code: 'validation_error',
        message: 'x',
        fields: { first_name: ['bad'] },
        field_codes: { first_name: ['invalid_name'] },
        current_plan: { id: 1 },
      }),
    );

    const error = await api.get('/me').catch((caught) => caught);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe('validation_error');
    expect(error.fieldCodes).toEqual({ firstName: ['invalid_name'] });
    expect(error.extra).toEqual({ currentPlan: { id: 1 } });
  });

  it('refreshes once for concurrent 401s and retries the requests', async () => {
    tokens.startSession('old');
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'new' } });
    adapter.mockImplementation((config) =>
      config.headers.Authorization === 'Bearer new'
        ? respond(config, 200, { ok: true })
        : respond(config, 401, { code: 'token_not_valid' }),
    );

    const results = await Promise.all([api.get('/me'), api.get('/me/training-plan')]);

    expect(refresh).toHaveBeenCalledTimes(1);
    // The refresh token travels in the httpOnly cookie, never in the body.
    expect(refresh.mock.calls[0][1]).toEqual({});
    expect(refresh.mock.calls[0][2]).toMatchObject({
      withCredentials: true,
      headers: { 'X-Requested-With': 'entrenanutricion' },
    });
    expect(results.map((result) => result.data)).toEqual([{ ok: true }, { ok: true }]);
    expect(tokens.getAccess()).toBe('new');
  });

  it('never sends a token: the one of an older version is deleted, not used', async () => {
    localStorage.setItem('entrenanutricion.refresh', 'legacy-refresh');
    const refresh = vi.spyOn(axios, 'post').mockResolvedValue({ data: { access: 'new' } });

    await refreshAccessToken();

    expect(refresh.mock.calls[0][1]).toEqual({});
    expect(localStorage.getItem('entrenanutricion.refresh')).toBeNull();
    expect(tokens.hasSession()).toBe(true);
  });

  it('logs out when the refresh fails', async () => {
    const expired = vi.fn();
    setSessionExpiredHandler(expired);
    tokens.startSession('old');
    vi.spyOn(axios, 'post').mockImplementation(() =>
      respond({ headers: {} } as InternalAxiosRequestConfig, 401, { code: 'token_not_valid' }),
    );
    adapter.mockImplementation((config) => respond(config, 401, { code: 'token_not_valid' }));

    await expect(api.get('/me')).rejects.toBeInstanceOf(ApiError);

    expect(expired).toHaveBeenCalled();
    expect(tokens.hasSession()).toBe(false);
  });

  it('tries again when another tab has just renewed the session', async () => {
    const expired = vi.fn();
    setSessionExpiredHandler(expired);
    tokens.startSession('old');
    const refresh = vi
      .spyOn(axios, 'post')
      .mockImplementationOnce(() =>
        respond({ headers: {} } as InternalAxiosRequestConfig, 401, { code: 'token_not_valid' }),
      )
      .mockResolvedValueOnce({ data: { access: 'new' } });
    adapter.mockImplementation((config) =>
      config.headers.Authorization === 'Bearer new'
        ? respond(config, 200, { id: 1 })
        : respond(config, 401, { code: 'token_not_valid' }),
    );

    await expect(api.get('/me')).resolves.toMatchObject({ data: { id: 1 } });

    expect(refresh).toHaveBeenCalledTimes(2);
    expect(expired).not.toHaveBeenCalled();
    expect(tokens.hasSession()).toBe(true);
  });

  it.each([
    [429, 'throttled'],
    [503, 'server_error'],
  ])('keeps the session when the refresh fails with a %i', async (status, code) => {
    const expired = vi.fn();
    setSessionExpiredHandler(expired);
    tokens.startSession('old');
    vi.spyOn(axios, 'post').mockImplementation(() =>
      respond({ headers: {} } as InternalAxiosRequestConfig, status, { code }),
    );
    adapter.mockImplementation((config) => respond(config, 401, { code: 'token_not_valid' }));

    await expect(api.get('/me')).rejects.toMatchObject({ code });

    expect(expired).not.toHaveBeenCalled();
    expect(tokens.hasSession()).toBe(true);
  });

  it('does not try to refresh on login failures', async () => {
    const refresh = vi.spyOn(axios, 'post');
    adapter.mockImplementation((config) => respond(config, 401, { code: 'invalid_credentials' }));

    const error = await api.post('/auth/login', {}).catch((caught) => caught);

    expect(error.code).toBe('invalid_credentials');
    expect(refresh).not.toHaveBeenCalled();
  });

  it('reports network errors', async () => {
    adapter.mockImplementation((config) => Promise.reject(new AxiosError('down', 'ERR', config)));

    const error = await api.get('/me').catch((caught) => caught);

    expect(error.code).toBe('network_error');
  });
});
