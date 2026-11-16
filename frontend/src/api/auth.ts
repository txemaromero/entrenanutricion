import { api } from './client';
import type { AuthResponse, PasswordResetInput, RegisterInput } from './types';

export const authApi = {
  login: (email: string, password: string, rememberMe: boolean) =>
    api.post<AuthResponse>('/auth/login', { email, password, rememberMe }).then((r) => r.data),

  register: (input: RegisterInput) =>
    api.post<AuthResponse>('/auth/register', input).then((r) => r.data),

  /** Blacklists the session's refresh token and deletes its cookie. */
  logout: () => api.post('/auth/logout'),

  /** Always succeeds (204) so the response never reveals whether the account exists. */
  requestPasswordReset: (email: string) => api.post('/auth/password-reset', { email }),

  confirmPasswordReset: (input: PasswordResetInput) =>
    api.post('/auth/password-reset/confirm', input),

  /** Open link of the verification email (signed in or not). */
  verifyEmail: (token: string) => api.post('/auth/verify-email', { token }),

  emailExists: (email: string) =>
    api
      .get<{ exists: boolean }>('/auth/email-exists', { params: { email } })
      .then((r) => r.data.exists),
};
