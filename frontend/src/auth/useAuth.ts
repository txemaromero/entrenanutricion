import { createContext, useContext } from 'react';

import type { Me, RegisterInput } from '../api/types';

export interface AuthContextValue {
  user: Me | null;
  initializing: boolean;
  sessionExpired: boolean;
  login: (email: string, password: string, rememberMe: boolean) => Promise<Me>;
  register: (input: RegisterInput) => Promise<Me>;
  logout: () => Promise<void>;
  /** Reload the current user from the API (after onboarding, profile edits…). */
  refreshUser: () => Promise<Me | null>;
  /** Replace the user with a fresh copy returned by another endpoint. */
  setUser: (user: Me) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>');
  return context;
};
