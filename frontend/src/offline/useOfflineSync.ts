import { useIonToast } from '@ionic/react';
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { trainingApi } from '../api/client-features';
import { flushOutbox } from './outbox';

/** Sends the marks made without coverage on start and whenever the browser is back online. */
export const useOfflineSync = (enabled: boolean) => {
  const { t } = useTranslation();
  const [toast] = useIonToast();

  useEffect(() => {
    if (!enabled) return;
    const sync = async () => {
      const { sent } = await flushOutbox((mark) =>
        trainingApi.setExerciseDone(mark.workoutId, mark.itemId, mark.completed, mark.sets),
      );
      if (sent > 0) void toast({ message: t('offline.synced'), duration: 2500, color: 'success' });
    };
    void sync();
    window.addEventListener('online', sync);
    return () => window.removeEventListener('online', sync);
  }, [enabled, t, toast]);
};
