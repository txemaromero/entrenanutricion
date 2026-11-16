import { useEffect, useState } from 'react';

import { OUTBOX_EVENT, pendingMarks } from './outbox';

/** Whether the browser has a connection (it reacts to going offline and back online). */
export const useOnline = (): boolean => {
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
    return () => {
      window.removeEventListener('online', update);
      window.removeEventListener('offline', update);
    };
  }, []);
  return online;
};

/** Number of exercise marks waiting to be sent. */
export const usePendingCount = (): number => {
  const [count, setCount] = useState(() => pendingMarks().length);
  useEffect(() => {
    const update = () => setCount(pendingMarks().length);
    window.addEventListener(OUTBOX_EVENT, update);
    return () => window.removeEventListener(OUTBOX_EVENT, update);
  }, []);
  return count;
};
