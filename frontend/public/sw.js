/* Basic service worker: caches the app shell and hashed static assets (page chunks included), so
 * the app opens without coverage. API calls and media are never cached here: the offline copies
 * of the client's plan live in the app (src/offline, cleared on logout). Bump CACHE to drop old
 * caches. */
const CACHE = 'entrenanutricion-v3';
const SHELL = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/manifest.en.webmanifest',
  '/manifest.ca.webmanifest',
  '/favicon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];
// Only the build's static files (scripts, styles, fonts and images), and only when the server
// answers with one: a host's SPA fallback (index.html for a missing file) is never kept as one.
const ASSET_PATH = /^\/assets\/[\w.-]+\.(?:js|css|woff2?|ttf|otf|png|jpe?g|webp|gif|svg|ico)$/;
const ASSET_TYPE = /^(?:text\/css|(?:text|application)\/javascript|font\/|image\/)/;

const cacheable = (pathname, response) => {
  if (!response.ok || response.type !== 'basic') return false;
  if (SHELL.includes(pathname)) return true;
  return ASSET_TYPE.test(response.headers.get('Content-Type') || '');
};

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))),
      ),
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/media/')) return;

  // Pages: network first so deploys are picked up, cached shell when offline.
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).catch(() => caches.match('/index.html')));
    return;
  }

  // Hashed assets and shell files: cache first.
  if (ASSET_PATH.test(url.pathname) || SHELL.includes(url.pathname)) {
    event.respondWith(
      caches.match(request).then(
        (cached) =>
          cached ||
          fetch(request).then((response) => {
            if (cacheable(url.pathname, response)) {
              const copy = response.clone();
              caches.open(CACHE).then((cache) => cache.put(request, copy));
            }
            return response;
          }),
      ),
    );
  }
});
