import { useIonRouter } from '@ionic/react';
import { useCallback } from 'react';

/**
 * Where to go after saving a form. Edits go back to the page that opened the form (it reloads
 * when re-entered); creations replace the form with the new item's page. Pushing a route that is
 * already in Ionic's stack with "replace" does not navigate, hence the split.
 */
export const useLeaveForm = (fallback: string) => {
  const router = useIonRouter();
  return useCallback(
    (createdHref?: string) => {
      if (createdHref) router.push(createdHref, 'forward', 'replace');
      else if (router.canGoBack()) router.goBack();
      else router.push(fallback, 'back', 'replace');
    },
    [router, fallback],
  );
};
