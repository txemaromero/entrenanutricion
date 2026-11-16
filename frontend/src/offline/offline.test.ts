import { ApiError } from '../api/errors';
import { enqueueMark, flushOutbox, pendingMarks } from './outbox';
import { offlineStore, withOfflineCopy } from './store';

const networkError = () => new ApiError({ status: 0, code: 'network_error' });

describe('offline copies', () => {
  beforeEach(() => {
    localStorage.clear();
    offlineStore.setOwner(7);
  });

  it('keeps one copy per user and clears them all', () => {
    offlineStore.write('training-plan', { id: 1 });
    offlineStore.setOwner(8);
    expect(offlineStore.read('training-plan')).toBeNull();
    offlineStore.setOwner(7);
    expect(offlineStore.read('training-plan')).toEqual({ id: 1 });

    offlineStore.clearAll();
    expect(offlineStore.read('training-plan')).toBeNull();
  });

  it('serves the last copy only when the network is down', async () => {
    const load = vi.fn().mockResolvedValueOnce({ id: 1 });
    const plan = withOfflineCopy('training-plan', load);
    expect(await plan()).toEqual({ id: 1 });

    load.mockRejectedValueOnce(networkError());
    expect(await plan()).toEqual({ id: 1 });

    load.mockRejectedValueOnce(new ApiError({ status: 404, code: 'not_found' }));
    await expect(plan()).rejects.toMatchObject({ code: 'not_found' });
  });

  it('without a copy the network error reaches the page', async () => {
    const plan = withOfflineCopy('other', () => Promise.reject(networkError()));
    await expect(plan()).rejects.toMatchObject({ code: 'network_error' });
  });
});

describe('outbox of exercise marks', () => {
  beforeEach(() => {
    localStorage.clear();
    offlineStore.setOwner(7);
  });

  it('keeps the last change of each exercise', () => {
    enqueueMark({ workoutId: 1, itemId: 10, completed: true });
    enqueueMark({ workoutId: 1, itemId: 11, completed: true });
    enqueueMark({ workoutId: 1, itemId: 10, completed: false });

    expect(pendingMarks()).toEqual([
      { workoutId: 1, itemId: 11, completed: true },
      { workoutId: 1, itemId: 10, completed: false },
    ]);
  });

  it('sends in order, stops on a network error and drops rejected marks', async () => {
    enqueueMark({ workoutId: 1, itemId: 10, completed: true });
    enqueueMark({ workoutId: 2, itemId: 20, completed: true });
    enqueueMark({ workoutId: 3, itemId: 30, completed: true });
    const send = vi
      .fn()
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new ApiError({ status: 409, code: 'workout_already_completed' }))
      .mockRejectedValueOnce(networkError());

    expect(await flushOutbox(send)).toEqual({ sent: 1, dropped: 1 });
    expect(pendingMarks()).toEqual([{ workoutId: 3, itemId: 30, completed: true }]);

    send.mockResolvedValueOnce({});
    expect(await flushOutbox(send)).toEqual({ sent: 1, dropped: 0 });
    expect(pendingMarks()).toEqual([]);
  });
});
