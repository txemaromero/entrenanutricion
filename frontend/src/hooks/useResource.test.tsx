import { act, renderHook, waitFor } from '@testing-library/react';

import { useResource } from './useResource';

const deferred = <T,>() => {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => (resolve = done));
  return { promise, resolve };
};

describe('useResource', () => {
  it('loads data on mount', async () => {
    const { result } = renderHook(() => useResource(() => Promise.resolve(['a'])));

    await waitFor(() => expect(result.current.data).toEqual(['a']));
    expect(result.current.loading).toBe(false);
  });

  it('reports errors as ApiError', async () => {
    const { result } = renderHook(() => useResource(() => Promise.reject(new Error('boom'))));

    await waitFor(() => expect(result.current.error?.code).toBe('unknown_error'));
  });

  it('ignores a slower, older response once a newer request was made', async () => {
    const slow = deferred<string>();
    const fast = deferred<string>();
    const calls = [slow, fast];
    const { result, rerender } = renderHook(
      ({ query }) => useResource(() => calls.shift()!.promise, [query]),
      {
        initialProps: { query: '' },
      },
    );

    rerender({ query: 'ana' });
    await act(async () => fast.resolve('filtered'));
    await act(async () => slow.resolve('everything'));

    expect(result.current.data).toBe('filtered');
  });
});
