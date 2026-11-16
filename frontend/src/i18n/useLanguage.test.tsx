import { act, renderHook } from '@testing-library/react';

import i18n from './index';
import { useLanguage } from './useLanguage';

describe('useLanguage', () => {
  beforeEach(() => {
    document.head.innerHTML =
      '<link rel="manifest" href="/manifest.webmanifest" /><meta name="description" content="" />';
  });

  afterEach(async () => {
    await i18n.changeLanguage('es');
  });

  it('switches language instantly and persists it', async () => {
    const { result } = renderHook(() => useLanguage());
    expect(result.current.language).toBe('es');

    await act(() => result.current.changeLanguage('ca'));

    expect(i18n.language).toBe('ca');
    expect(i18n.t('tabs.profile')).toBe('Perfil');
    expect(i18n.t('common.save')).toBe('Desar');
    expect(localStorage.getItem('entrenanutricion.language')).toBe('ca');
    expect(document.documentElement.lang).toBe('ca');
    // The installed app (manifest) and the page description follow the language.
    expect(document.querySelector('link[rel="manifest"]')).toHaveAttribute(
      'href',
      '/manifest.ca.webmanifest',
    );
    expect(document.querySelector('meta[name="description"]')).toHaveAttribute(
      'content',
      "Plans d'entrenament i nutrició personalitzats",
    );
  });

  it('keeps working when storage is blocked', async () => {
    const spy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked');
    });
    const { result } = renderHook(() => useLanguage());

    await act(() => result.current.changeLanguage('en'));

    expect(i18n.language).toBe('en');
    spy.mockRestore();
  });
});
