import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react';

// Tiny query cache shared across screens (e.g. the chart is fetched once per
// profile and reused by the Chart, Planets and Panchang sections).
// Entries are immutable snapshots consumed through useSyncExternalStore.

const EMPTY = Object.freeze({ data: undefined, error: null, refreshing: false });
const entries = new Map();   // key -> { data, error, refreshing }
const listeners = new Map(); // key -> Set<() => void>
const fetchers = new Map();  // key -> () => Promise
const inflight = new Map();  // key -> Promise

function setEntry(key, patch) {
  entries.set(key, { ...(entries.get(key) || EMPTY), ...patch });
  listeners.get(key)?.forEach((l) => l());
}

function load(key, { refresh = false } = {}) {
  const fetcher = fetchers.get(key);
  if (!fetcher) return Promise.resolve();
  if (inflight.has(key) && !refresh) return inflight.get(key);
  const hasData = entries.get(key)?.data !== undefined;
  setEntry(key, { error: null, refreshing: refresh && hasData });
  const p = (async () => {
    try {
      setEntry(key, { data: await fetcher(), refreshing: false });
    } catch (error) {
      setEntry(key, { error, refreshing: false });
    } finally {
      inflight.delete(key);
    }
  })();
  inflight.set(key, p);
  return p;
}

/**
 * Drop cached entries whose key starts with `prefix`; mounted screens refetch.
 * With `{ keep: true }`, mounted screens keep showing the current data while it refreshes in the
 * background (no spinner); unmounted entries are still dropped so they load fresh next time.
 */
export function invalidate(prefix, { keep = false } = {}) {
  for (const key of [...entries.keys()]) {
    if (!key.startsWith(prefix)) continue;
    const watched = listeners.get(key)?.size;
    if (keep && watched && entries.get(key)?.data !== undefined) {
      load(key, { refresh: true });
      continue;
    }
    entries.delete(key);
    if (watched) load(key);
  }
}

/** Used on sign-out: drop everything silently (protected screens unmount anyway). */
export function invalidateAll() {
  entries.clear();
  inflight.clear();
}

export function setCached(key, data) {
  setEntry(key, { data, error: null, refreshing: false });
}

/** Update a cached entry from its latest value (safe when several updates overlap). */
export function updateCached(key, fn) {
  const data = entries.get(key)?.data;
  if (data !== undefined) setEntry(key, { data: fn(data) });
}

/**
 * useApi('p:123:chart', () => vedicApi.chart(id)) -> { data, error, loading, refreshing, refetch }
 * Pass key = null to skip.
 */
export function useApi(key, fetcher) {
  const fetcherRef = useRef(fetcher);
  useEffect(() => { fetcherRef.current = fetcher; });

  const subscribe = useCallback((cb) => {
    if (!key) return () => {};
    if (!listeners.has(key)) listeners.set(key, new Set());
    listeners.get(key).add(cb);
    return () => listeners.get(key)?.delete(cb);
  }, [key]);
  const getSnapshot = useCallback(() => (key ? entries.get(key) || EMPTY : EMPTY), [key]);
  const state = useSyncExternalStore(subscribe, getSnapshot);

  useEffect(() => {
    if (!key) return;
    fetchers.set(key, () => fetcherRef.current());
    const e = entries.get(key);
    if (!e || (e.data === undefined && !e.error)) load(key);
  }, [key]);

  const refetch = useCallback(() => (key ? load(key, { refresh: true }) : Promise.resolve()), [key]);

  return {
    data: state.data,
    error: state.error,
    loading: !!key && state.data === undefined && !state.error,
    refreshing: state.refreshing,
    refetch,
  };
}
