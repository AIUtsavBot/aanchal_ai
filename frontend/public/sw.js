const CACHE_NAME = 'aanchal-ai-cache-v1';
const urlsToCache = [
    '/',
    '/index.html',
    '/manifest.json',
    '/favicon.ico',
];

// Install Event - cache core resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened offline PWA cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch Event - network first, falling back to cache
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    // Ignore API calls, we only cache static assets
    if (event.request.url.includes('/api/')) return;

    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clone the response because it's a stream
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request, responseClone);
                });
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

// Activate Event - clean up old caches
self.addEventListener('activate', event => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
