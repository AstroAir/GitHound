/**
 * Service Worker for GitHound Frontend
 * Provides caching, offline support, and performance optimization
 */

const CACHE_NAME = 'githound-v2.0.0-1757866225277';
const STATIC_CACHE = 'githound-static-v1.0.0';
const DYNAMIC_CACHE = 'githound-dynamic-v1.0.0';
const API_CACHE = 'githound-api-v1.0.0';

// Files to cache immediately
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/main.js',
  '/styles/main.css',
  '/components/core/component.js',
  '/components/core/registry.js',
  '/components/core/event-bus.js',
  '/components/core/state-manager.js',
  '/components/core/app.js',
  '/utils/api.js',
  '/utils/dom.js'
];

// API endpoints to cache
const CACHEABLE_APIS = [
  '/api/health',
  '/api/user/profile',
  '/api/search/templates'
];

// Cache strategies
const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
  NETWORK_ONLY: 'network-only',
  CACHE_ONLY: 'cache-only'
};

// Route configurations
const ROUTE_CONFIG = {
  // Static assets - cache first
  '/components/': CACHE_STRATEGIES.CACHE_FIRST,
  '/utils/': CACHE_STRATEGIES.CACHE_FIRST,
  '/styles/': CACHE_STRATEGIES.CACHE_FIRST,

  // API endpoints - network first with fallback
  '/api/search': CACHE_STRATEGIES.NETWORK_FIRST,
  '/api/user': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,
  '/api/health': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,

  // WebSocket - network only
  '/ws': CACHE_STRATEGIES.NETWORK_ONLY,

  // Main app - stale while revalidate
  '/': CACHE_STRATEGIES.STALE_WHILE_REVALIDATE
};

/**
 * Install event - cache static assets
 */
self.addEventListener('install', event => {
  console.log('Service Worker: Installing...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Static assets cached');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Service Worker: Failed to cache static assets', error);
      })
  );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', event => {
  console.log('Service Worker: Activating...');

  event.waitUntil(
    caches.keys()
      .then(cacheNames => Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE
                && cacheName !== DYNAMIC_CACHE
                && cacheName !== API_CACHE) {
            console.log('Service Worker: Deleting old cache', cacheName);
            return caches.delete(cacheName);
          }
        })
      ))
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim();
      })
  );
});

/**
 * Fetch event - handle requests with appropriate caching strategy
 */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip WebSocket requests
  if (url.protocol === 'ws:' || url.protocol === 'wss:') {
    return;
  }

  // Determine cache strategy
  const strategy = getCacheStrategy(url.pathname);

  event.respondWith(
    handleRequest(request, strategy)
      .catch(error => {
        console.error('Service Worker: Request failed', error);
        return createErrorResponse(request);
      })
  );
});

/**
 * Get cache strategy for a given path
 * @param {string} pathname - Request pathname
 * @returns {string} Cache strategy
 */
function getCacheStrategy(pathname) {
  for (const [route, strategy] of Object.entries(ROUTE_CONFIG)) {
    if (pathname.startsWith(route)) {
      return strategy;
    }
  }

  // Default strategy
  return CACHE_STRATEGIES.STALE_WHILE_REVALIDATE;
}

/**
 * Handle request with specified strategy
 * @param {Request} request - Fetch request
 * @param {string} strategy - Cache strategy
 * @returns {Promise<Response>} Response promise
 */
async function handleRequest(request, strategy) {
  switch (strategy) {
    case CACHE_STRATEGIES.CACHE_FIRST:
      return cacheFirst(request);

    case CACHE_STRATEGIES.NETWORK_FIRST:
      return networkFirst(request);

    case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
      return staleWhileRevalidate(request);

    case CACHE_STRATEGIES.NETWORK_ONLY:
      return fetch(request);

    case CACHE_STRATEGIES.CACHE_ONLY:
      return cacheOnly(request);

    default:
      return staleWhileRevalidate(request);
  }
}

/**
 * Cache first strategy
 * @param {Request} request - Fetch request
 * @returns {Promise<Response>} Response promise
 */
async function cacheFirst(request) {
  const cachedResponse = await getCachedResponse(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  const networkResponse = await fetch(request);
  await cacheResponse(request, networkResponse.clone());

  return networkResponse;
}

/**
 * Network first strategy
 * @param {Request} request - Fetch request
 * @returns {Promise<Response>} Response promise
 */
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    await cacheResponse(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    const cachedResponse = await getCachedResponse(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

/**
 * Stale while revalidate strategy
 * @param {Request} request - Fetch request
 * @returns {Promise<Response>} Response promise
 */
async function staleWhileRevalidate(request) {
  const cachedResponse = await getCachedResponse(request);

  // Start network request in background
  const networkPromise = fetch(request)
    .then(response => {
      cacheResponse(request, response.clone());
      return response;
    })
    .catch(error => {
      console.warn('Service Worker: Network request failed', error);
    });

  // Return cached response immediately if available
  if (cachedResponse) {
    return cachedResponse;
  }

  // Wait for network response if no cache
  return networkPromise;
}

/**
 * Cache only strategy
 * @param {Request} request - Fetch request
 * @returns {Promise<Response>} Response promise
 */
async function cacheOnly(request) {
  const cachedResponse = await getCachedResponse(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  throw new Error('No cached response available');
}

/**
 * Get cached response
 * @param {Request} request - Fetch request
 * @returns {Promise<Response|null>} Cached response or null
 */
async function getCachedResponse(request) {
  const cacheNames = [STATIC_CACHE, DYNAMIC_CACHE, API_CACHE];

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const response = await cache.match(request);

    if (response) {
      return response;
    }
  }

  return null;
}

/**
 * Cache response
 * @param {Request} request - Original request
 * @param {Response} response - Response to cache
 */
async function cacheResponse(request, response) {
  if (!response || response.status !== 200 || response.type !== 'basic') {
    return;
  }

  const url = new URL(request.url);
  let cacheName;

  // Determine appropriate cache
  if (url.pathname.startsWith('/api/')) {
    cacheName = API_CACHE;
  } else if (STATIC_ASSETS.some(asset => url.pathname.includes(asset))) {
    cacheName = STATIC_CACHE;
  } else {
    cacheName = DYNAMIC_CACHE;
  }

  const cache = await caches.open(cacheName);
  await cache.put(request, response);
}

/**
 * Create error response
 * @param {Request} request - Original request
 * @returns {Response} Error response
 */
function createErrorResponse(request) {
  const url = new URL(request.url);

  if (url.pathname.startsWith('/api/')) {
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: 'Please check your internet connection'
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  // For HTML requests, return offline page
  return new Response(
    `
    <!DOCTYPE html>
    <html>
    <head>
      <title>GitHound - Offline</title>
      <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .offline { color: #666; }
      </style>
    </head>
    <body>
      <div class="offline">
        <h1>You're offline</h1>
        <p>Please check your internet connection and try again.</p>
        <button onclick="window.location.reload()">Retry</button>
      </div>
    </body>
    </html>
    `,
    {
      status: 503,
      statusText: 'Service Unavailable',
      headers: { 'Content-Type': 'text/html' }
    }
  );
}

/**
 * Message event - handle messages from main thread
 */
self.addEventListener('message', event => {
  const { type, data } = event.data;

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;

    case 'CACHE_URLS':
      cacheUrls(data.urls);
      break;

    case 'CLEAR_CACHE':
      clearCache(data.cacheName);
      break;

    case 'GET_CACHE_INFO':
      getCacheInfo().then(info => {
        event.ports[0].postMessage(info);
      });
      break;
  }
});

/**
 * Cache specific URLs
 * @param {Array} urls - URLs to cache
 */
async function cacheUrls(urls) {
  const cache = await caches.open(DYNAMIC_CACHE);
  await cache.addAll(urls);
}

/**
 * Clear specific cache
 * @param {string} cacheName - Cache name to clear
 */
async function clearCache(cacheName) {
  await caches.delete(cacheName);
}

/**
 * Get cache information
 * @returns {Promise<Object>} Cache information
 */
async function getCacheInfo() {
  const cacheNames = await caches.keys();
  const info = {};

  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    info[cacheName] = keys.length;
  }

  return info;
}
