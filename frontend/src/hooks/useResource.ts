import { useIonViewWillEnter } from '@ionic/react';
import { useCallback, useEffect, useRef, useState } from 'react';

import { ApiError, toApiError } from '../api/errors';
import i18n from '../i18n';

interface ResourceState<T> {
  data: T | undefined;
  error: ApiError | undefined;
  loading: boolean;
}

/**
 * Load data for a page and reload it every time the view is entered again, so Ionic's cached
 * pages never show stale data after edits made elsewhere.
 */
export const useResource = <T>(loader: () => Promise<T>, deps: unknown[] = []) => {
  const [state, setState] = useState<ResourceState<T>>({
    data: undefined,
    error: undefined,
    loading: true,
  });
  const loaderRef = useRef(loader);
  const mounted = useRef(true);
  const firstLoadDone = useRef(false);
  // Only the latest request may update the state: an older, slower response (e.g. the
  // reload on view enter) must not overwrite newer data (e.g. a search typed meanwhile).
  const latestRequest = useRef(0);

  useEffect(() => {
    loaderRef.current = loader;
  });

  const fetchData = useCallback(async () => {
    const request = ++latestRequest.current;
    const isCurrent = () => mounted.current && request === latestRequest.current;
    try {
      const data = await loaderRef.current();
      if (isCurrent()) setState({ data, error: undefined, loading: false });
      return data;
    } catch (error) {
      if (isCurrent()) setState({ data: undefined, error: toApiError(error), loading: false });
      return undefined;
    } finally {
      firstLoadDone.current = true;
    }
  }, []);

  const reload = useCallback(() => {
    setState((previous) => ({ ...previous, loading: true, error: undefined }));
    return fetchData();
  }, [fetchData]);

  useEffect(() => {
    mounted.current = true;
    void fetchData();
    return () => {
      mounted.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload when the caller's deps change
  }, deps);

  useIonViewWillEnter(() => {
    if (firstLoadDone.current) void fetchData();
  });

  // Catalog texts come in the language of the request: ask again when the language changes.
  useEffect(() => {
    const onLanguageChanged = () => {
      if (firstLoadDone.current) void fetchData();
    };
    i18n.on('languageChanged', onLanguageChanged);
    return () => i18n.off('languageChanged', onLanguageChanged);
  }, [fetchData]);

  const setData = useCallback(
    (data: T) => setState({ data, error: undefined, loading: false }),
    [],
  );

  return { ...state, reload, setData };
};
