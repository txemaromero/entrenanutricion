import { act, renderHook, waitFor } from '@testing-library/react';

import { meApi } from '../api/me';
import type { Me } from '../api/types';
import i18n from '../i18n';
import { useAccountLanguage } from './useAccountLanguage';

const me = (language: Me['language']) => ({ id: 1, language }) as Me;

describe('useAccountLanguage', () => {
  afterEach(async () => {
    vi.restoreAllMocks();
    await act(() => i18n.changeLanguage('es'));
  });

  it('sends the language of the app when the account has another one', async () => {
    const update = vi.spyOn(meApi, 'updateProfile').mockResolvedValue(me('es'));
    const onSaved = vi.fn();

    renderHook(() => useAccountLanguage(me('ca'), onSaved));

    await waitFor(() => expect(update).toHaveBeenCalledWith({ language: 'es' }));
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(me('es')));
  });

  it('follows the language menu and does nothing when they match', async () => {
    const update = vi.spyOn(meApi, 'updateProfile').mockResolvedValue(me('en'));
    const { rerender } = renderHook(({ user }) => useAccountLanguage(user, vi.fn()), {
      initialProps: { user: me('es') },
    });
    expect(update).not.toHaveBeenCalled();

    await act(() => i18n.changeLanguage('en'));
    rerender({ user: me('es') });

    await waitFor(() => expect(update).toHaveBeenCalledWith({ language: 'en' }));
  });

  it('nobody signed in: nothing to send', () => {
    const update = vi.spyOn(meApi, 'updateProfile');

    renderHook(() => useAccountLanguage(null, vi.fn()));

    expect(update).not.toHaveBeenCalled();
  });
});
