const cache = new Map<string, Promise<any>>();

/** Return cached JSON promise for url, or fetch + cache it. */
export function fetchCached(url: string): Promise<any> {
  let entry = cache.get(url);
  if (!entry) {
    entry = fetch(url).then((r) => r.json());
    cache.set(url, entry);
  }
  return entry;
}

/** Clear the client-side cache so the next fetchCached() call re-fetches. */
export function invalidateCache() {
  cache.clear();
}

/** Fire off all list-page fetches so they're warm when the user switches tabs. */
export function preloadAll() {
  fetchCached("/api/search?q=&all=datasets");
  fetchCached("/api/vendors");
  fetchCached("/api/search?all=fields");
  fetchCached("/api/monikers?depth=1");
}
