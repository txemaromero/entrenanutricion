import { ApiError } from '../api/errors';
import type { SetEntry } from '../api/types';
import { isNetworkError, offlineStore } from './store';

/**
 * Exercises marked as done without coverage wait here and are sent when the connection
 * returns. One entry per exercise of a workout: the last change wins.
 */
export interface PendingMark {
  workoutId: number;
  itemId: number;
  completed: boolean;
  /** Sets done so far, when they were logged without coverage. */
  sets?: SetEntry[];
}

const KEY = 'outbox';
export const OUTBOX_EVENT = 'entrenanutricion:outbox';

const read = (): PendingMark[] => offlineStore.read<PendingMark[]>(KEY) ?? [];

const save = (marks: PendingMark[]) => {
  offlineStore.write(KEY, marks);
  window.dispatchEvent(new Event(OUTBOX_EVENT));
};

export const pendingMarks = (): PendingMark[] => read();

export const enqueueMark = (mark: PendingMark) => {
  const isSame = (pending: PendingMark) =>
    pending.workoutId === mark.workoutId && pending.itemId === mark.itemId;
  const previous = read().find(isSame);
  // A later checkbox change keeps the sets logged offline before it.
  const merged = mark.sets || !previous?.sets ? mark : { ...mark, sets: previous.sets };
  save([...read().filter((pending) => !isSame(pending)), merged]);
};

let flushing: Promise<{ sent: number; dropped: number }> | null = null;

/**
 * Send the pending marks in order. A network error stops (the rest wait for the next try);
 * an answer from the API that rejects a mark (workout finished, plan changed…) drops it.
 */
export const flushOutbox = (
  send: (mark: PendingMark) => Promise<unknown>,
): Promise<{ sent: number; dropped: number }> => {
  if (!flushing) {
    flushing = (async () => {
      let sent = 0;
      let dropped = 0;
      for (const mark of read()) {
        try {
          await send(mark);
          sent += 1;
        } catch (error) {
          if (isNetworkError(error) || !(error instanceof ApiError)) break;
          dropped += 1;
        }
        save(read().filter((pending) => !same(pending, mark)));
      }
      return { sent, dropped };
    })().finally(() => {
      flushing = null;
    });
  }
  return flushing;
};

const same = (a: PendingMark, b: PendingMark) =>
  a.workoutId === b.workoutId &&
  a.itemId === b.itemId &&
  a.completed === b.completed &&
  JSON.stringify(a.sets) === JSON.stringify(b.sets);
