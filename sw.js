const CACHE_NAME = "cochin-ri-pwa-v31";
const ASSETS = [
  "./",
  "./index.html",
  "./manifest.json?v=2",
  "./apple-touch-icon.png?v=2",
  "./icon-192.png?v=2",
  "./icon-512.png?v=2"
];

self.addEventListener("install", event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      for (const url of ASSETS) {
        try {
          const res = await fetch(url, { cache: "no-store" });
          if (res.ok) await cache.put(url, res);
        } catch (_) {}
      }
    })
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
      .then(() => self.clients.matchAll({ type: "window" }))
      .then(clients => {
        for (const client of clients) {
          if ("navigate" in client) {
            client.navigate(client.url).catch(() => {});
          }
        }
      })
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET" || req.url.includes("supabase.co")) {
    return;
  }
  event.respondWith(
    fetch(req, { cache: "no-store" })
      .then(res => {
        const clone = res.clone();
        caches.open(CACHE_NAME).then(c => {
          c.put(req, clone);
          if (req.url.includes("index.html")) {
            c.put("./index.html", res.clone());
            c.put("./", res.clone());
          }
        });
        return res;
      })
      .catch(() => caches.match(req))
  );
});
