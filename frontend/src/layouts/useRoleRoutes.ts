import { useEffect, useState, type ComponentType } from 'react';

import type { Me } from '../api/types';
import { routesFor } from './appRoutes';

export interface LoadedRoute {
  path: string;
  exact?: boolean;
  component: ComponentType;
}

interface LoadState {
  key: string;
  routes?: LoadedRoute[];
  error?: unknown;
}

/**
 * Loads every page of the user's role (or client status) in parallel. Returns null routes
 * while loading; a failed load (offline, or chunks gone after a new deploy) sets `failed`.
 */
export const useRoleRoutes = (user: Me) => {
  const { key, routes } = routesFor(user);
  const [state, setState] = useState<LoadState | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all(
      routes.map(async (route) => ({
        path: route.path,
        exact: route.exact,
        component: await route.load(),
      })),
    )
      .then((loaded) => {
        if (!cancelled) setState({ key, routes: loaded });
      })
      .catch((error: unknown) => {
        if (!cancelled) setState({ key, error });
      });
    return () => {
      cancelled = true;
    };
    // `routes` is the same list for a given key.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const current = state?.key === key ? state : null;
  return { routes: current?.routes ?? null, failed: Boolean(current?.error) };
};
