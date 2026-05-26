const V = 'v8-' + Date.now();
self.addEventListener('install', e => {
  self.skipWaiting();
});
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});
// Network only — never cache, always fresh
self.addEventListener('fetch', e => {
  e.respondWith(fetch(e.request));
});
