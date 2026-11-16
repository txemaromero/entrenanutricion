import { act, render, screen } from '@testing-library/react';

import { offlineStore } from '../offline/store';
import { AuthProvider } from './AuthContext';
import { useAuth } from './useAuth';

const expiry = vi.hoisted(() => ({ handler: (): void => undefined }));

vi.mock('../api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/client')>()),
  setSessionExpiredHandler: (handler: () => void) => {
    expiry.handler = handler;
  },
}));

const Probe = () => {
  const { initializing, sessionExpired } = useAuth();
  const state = initializing ? 'loading' : sessionExpired ? 'expired' : 'open';
  return <p data-testid="state">{state}</p>;
};

const offlineKeys = () =>
  Object.keys(window.localStorage).filter((key) => key.startsWith('entrenanutricion.offline'));

describe('AuthProvider', () => {
  afterEach(() => {
    window.localStorage.clear();
    offlineStore.setOwner(null);
  });

  it('a session that expires leaves nothing of the account on the device', async () => {
    window.localStorage.setItem('entrenanutricion.offline.me', JSON.stringify({ id: 7 }));
    window.localStorage.setItem('entrenanutricion.offline.7.training-plan', '{"id": 1}');
    window.localStorage.setItem('entrenanutricion.offline.7.outbox', '[]');
    window.localStorage.setItem('entrenanutricion.language', 'ca');
    offlineStore.setOwner(7);
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    expect(await screen.findByTestId('state')).toHaveTextContent('open');

    act(() => expiry.handler());

    expect(screen.getByTestId('state')).toHaveTextContent('expired');
    expect(offlineKeys()).toEqual([]);
    expect(offlineStore.owner()).toBeNull();
    // Preferences of the device itself stay.
    expect(window.localStorage.getItem('entrenanutricion.language')).toBe('ca');
  });
});
