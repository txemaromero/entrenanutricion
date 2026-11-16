import { api } from './client';
import type {
  AccessToken,
  ConsentInput,
  Me,
  Onboarding,
  PasswordChangeInput,
  ProfileUpdateInput,
} from './types';

export const meApi = {
  get: () => api.get<Me>('/me').then((r) => r.data),

  updateProfile: (input: ProfileUpdateInput) =>
    api.patch<Me>('/me/profile', input).then((r) => r.data),

  changePassword: (input: PasswordChangeInput) =>
    api.put<AccessToken>('/me/password', input).then((r) => r.data),

  /** Send the verification link again (while the address is not confirmed). */
  resendVerification: () => api.post('/me/verify-email/resend'),

  /** Accept the current privacy policy (and, for clients, the use of health data). */
  consent: (input: ConsentInput) => api.post<Me>('/me/consent', input).then((r) => r.data),

  /** Every personal record as a JSON file (GDPR access and portability). */
  exportData: async () => {
    const response = await api.get<Blob>('/me/export', { responseType: 'blob' });
    const disposition = String(response.headers['content-disposition'] ?? '');
    const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? 'entrenanutricion-datos.json';
    return { blob: response.data, filename };
  },

  /** Right to erasure (clients): the account and all its data, confirmed with the password. */
  deleteAccount: (password: string) => api.delete('/me/account', { data: { password } }),

  uploadPhoto: (file: Blob, filename: string) => {
    const form = new FormData();
    form.append('photo', file, filename);
    return api.put<Me>('/me/photo', form).then((r) => r.data);
  },

  removePhoto: () => api.delete<Me>('/me/photo').then((r) => r.data),

  getOnboarding: () => api.get<Onboarding>('/me/onboarding').then((r) => r.data),

  submitOnboarding: (input: Onboarding) =>
    api.post<Onboarding>('/me/onboarding', input).then((r) => r.data),
};
