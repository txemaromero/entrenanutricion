import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { runInNewContext } from 'node:vm';

/** public/sw.js run in a sandbox with fake caches and network (it is a plain worker script). */

const ORIGIN = 'https://app.example.com';

interface FakeResponse {
  ok: boolean;
  type: string;
  headers: { get: (name: string) => string | null };
  clone: () => FakeResponse;
}

const answer = (contentType: string, { ok = true, type = 'basic' } = {}): FakeResponse => {
  const response: FakeResponse = {
    ok,
    type,
    headers: { get: (name) => (name.toLowerCase() === 'content-type' ? contentType : null) },
    clone: () => response,
  };
  return response;
};

type Listener = (event: Record<string, unknown>) => void;

const loadWorker = (network: Record<string, FakeResponse> = {}) => {
  const listeners: Record<string, Listener> = {};
  const stored: string[] = [];
  const deleted: string[] = [];
  const cache = {
    addAll: () => Promise.resolve(),
    put: (request: { url: string }) => {
      stored.push(new URL(request.url).pathname);
      return Promise.resolve();
    },
  };
  runInNewContext(readFileSync(resolve(__dirname, '../public/sw.js'), 'utf8'), {
    URL,
    self: {
      location: { origin: ORIGIN },
      addEventListener: (name: string, listener: Listener) => {
        listeners[name] = listener;
      },
      skipWaiting: () => undefined,
      clients: { claim: () => undefined },
    },
    caches: {
      open: () => Promise.resolve(cache),
      match: () => Promise.resolve(undefined),
      keys: () => Promise.resolve(['entrenanutricion-v2', 'entrenanutricion-v3']),
      delete: (key: string) => {
        deleted.push(key);
        return Promise.resolve(true);
      },
    },
    fetch: (request: { url: string }) => Promise.resolve(network[new URL(request.url).pathname]),
  });

  /** Whether the worker answers the request itself (true) or leaves it to the network. */
  const request = async (path: string, { method = 'GET', origin = ORIGIN } = {}) => {
    let handled: Promise<unknown> | undefined;
    listeners.fetch({
      request: { url: `${origin}${path}`, method, mode: 'no-cors' },
      respondWith: (promise: Promise<unknown>) => {
        handled = promise;
      },
    });
    if (handled) await handled;
    await new Promise((done) => setTimeout(done, 0)); // the copy is stored after answering
    return handled !== undefined;
  };

  return { listeners, stored, deleted, request };
};

describe('service worker', () => {
  it("keeps the build's scripts, styles, fonts and images", async () => {
    const network = {
      '/assets/index-B1x_9z.js': answer('text/javascript; charset=utf-8'),
      '/assets/index-Ab12.css': answer('text/css'),
      '/assets/inter-latin.woff2': answer('font/woff2'),
      '/assets/logo-9f8e.png': answer('image/png'),
    };
    const worker = loadWorker(network);

    for (const path of Object.keys(network)) {
      expect(await worker.request(path)).toBe(true);
    }
    expect(worker.stored).toEqual(Object.keys(network));
  });

  it('never keeps the page a host serves for a missing file, errors nor opaque answers', async () => {
    const worker = loadWorker({
      '/assets/index-gone.js': answer('text/html; charset=utf-8'), // SPA fallback (index.html)
      '/assets/broken-1.js': answer('text/javascript', { ok: false }),
      '/assets/other-2.js': answer('text/javascript', { type: 'opaque' }),
    });

    await worker.request('/assets/index-gone.js');
    await worker.request('/assets/broken-1.js');
    await worker.request('/assets/other-2.js');

    expect(worker.stored).toEqual([]);
  });

  it('leaves the API, the media, other files and other sites to the network', async () => {
    const worker = loadWorker();

    for (const path of [
      '/api/v1/me',
      '/media/profile_photos/a.png',
      '/assets/../api/v1/me',
      '/assets/nested/file.js',
      '/assets/notes.json',
      '/robots.txt',
    ]) {
      expect(await worker.request(path)).toBe(false);
    }
    expect(await worker.request('/assets/index-1.js', { method: 'POST' })).toBe(false);
    expect(await worker.request('/assets/index-1.js', { origin: 'https://cdn.example' })).toBe(
      false,
    );
  });

  it('drops the caches of older versions when it takes over', async () => {
    const worker = loadWorker();
    let done: Promise<unknown> = Promise.resolve();

    worker.listeners.activate({
      waitUntil: (promise: Promise<unknown>) => {
        done = promise;
      },
    });
    await done;

    expect(worker.deleted).toEqual(['entrenanutricion-v2']);
  });
});
