const CACHE_NAME = 'ario-shop-v12';
// Text font weights stay out of the install list: they are cached on first use
// by cacheFirst below, which keeps the install fast and light on mobile data.
const STATIC_ASSETS = [
    '/static/assets/css/ario-icons.css',
    '/static/assets/css/ar-tokens.css',
    '/static/assets/css/ar-core.css',
    '/static/assets/css/ar-components.css',
    '/static/assets/css/ar-pages.css',
    '/static/assets/fonts/molla0ab2.woff2',
    '/static/assets/js/ar.js',
    '/static/assets/images/icons/android-chrome-192x192.png',
    '/static/assets/images/icons/android-chrome-256x256.png',
    '/static/assets/images/icons/icon-512x512.png',
    '/static/assets/images/icons/apple-touch-icon.png',
    '/static/assets/images/icons/favicon-32x32.png',
    '/static/assets/images/icons/favicon-16x16.png',
    '/static/assets/images/v2/hero-main.webp',
    '/static/assets/images/v2/hero-main-640.webp',
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    if (request.method !== 'GET') return;

    if (url.pathname.startsWith('/admin') || url.pathname.startsWith('/accounts/') || url.pathname.startsWith('/cart/')) {
        return;
    }

    // Admin assets are edited often and must never be served from a stale cache.
    if (url.pathname.startsWith('/static/admin/')) {
        return;
    }

    if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
        event.respondWith(cacheFirst(request));
        return;
    }

    // HTML pages are always fetched fresh; only a plain offline notice is served.
    event.respondWith(networkOnly(request));
});

async function cacheFirst(request) {
    // Exact match (including ?v=) so a bumped asset version always comes from
    // the network instead of an older cached copy.
    const cached = await caches.match(request);
    if (cached) return cached;
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch {
        // Offline: a same-path older version is better than nothing.
        const fallback = await caches.match(request, { ignoreSearch: true });
        if (fallback) return fallback;
        return new Response('آفلاین', { status: 503, statusText: 'Offline' });
    }
}

async function networkOnly(request) {
    try {
        return await fetch(request);
    } catch {
        return new Response('اتصال اینترنت برقرار نیست.', {
            status: 503,
            statusText: 'Offline',
            headers: { 'Content-Type': 'text/plain; charset=utf-8' },
        });
    }
}
