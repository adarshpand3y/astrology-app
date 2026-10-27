import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react';

import { network } from '../network';

// Tiny query cache shared across screens (e.g. the chart is fetched once per
// profile and reused by the Chart, Planets and Panchang sections).
// Entries are immutable snapshots consumed through useSyncExternalStore.
//
// Every result is also saved on the phone so screens still show data offline. Saved
// results load at launch marked `stale` and are refetched as soon as a screen uses them
// while online; when a fetch fails for lack of connection, the saved data stays up.

const EMPTY = Object.freeze({ data: undefined, error: null, refreshing: false, stale: false });
const entries = new Map();   // key -> { data, error, refreshing, stale }
const listeners = new Map(); // key -> Set<() => void>
const fetchers = new Map();  // key -> () => Promise
const inflight = new Map();  // key -> Promise

const STORE_PREFIX = 'q1:';
const DAY_MS = 24 * 60 * 60 * 1000;
const MAX_AGE_MS = 7 * DAY_MS;
// Birth charts and the profile list only change when the user edits a profile.
const LONG_LIVED = ['p:', 'profiles'];
const LONG_MAX_AGE_MS = 30 * DAY_MS;
const OFFLINE_CODES = new Set(['network_error', 'timeout']);

const maxAge = (key) => (LONG_LIVED.some((p) => key.startsWith(p)) ? LONG_MAX_AGE_MS : MAX_AGE_MS);

function persist(key, data) {
  AsyncStorage.setItem(STORE_PREFIX + key, JSON.stringify({ at: Date.now(), data })).catch(() => {});
}

function unpersist(keys) {
  if (keys.length) AsyncStorage.multiRemove(keys.map((k) => STORE_PREFIX + k)).catch(() => {});
}

/** Load the saved results into memory (at launch, before screens mount); drops expired ones. */
export async function hydrateCache() {
  try {
    const keys = (await AsyncStorage.getAllKeys()).filter((k) => k.startsWith(STORE_PREFIX));
    const expired = [];
    for (const [storeKey, raw] of await AsyncStorage.multiGet(keys)) {
      const key = storeKey.slice(STORE_PREFIX.length);
      try {
        const { at, data } = JSON.parse(raw);
        if (Date.now() - at > maxAge(key) || data === undefined) expired.push(key);
        else if (!entries.has(key)) entries.set(key, { ...EMPTY, data, stale: true });
      } catch {
        expired.push(key);
      }
    }
    unpersist(expired);
  } catch { /* storage unavailable: run without the offline copy */ }
}

function setEntry(key, patch) {
  entries.set(key, { ...(entries.get(key) || EMPTY), ...patch });
  if (patch.data !== undefined) persist(key, patch.data);
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
      setEntry(key, { data: await fetcher(), refreshing: false, stale: false });
    } catch (error) {
      // No connection: keep showing what we have; it refetches when the phone is back online.
      if (OFFLINE_CODES.has(error.code) && entries.get(key)?.data !== undefined) setEntry(key, { refreshing: false, stale: true });
      else setEntry(key, { error, refreshing: false });
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
  const dropped = [];
  for (const key of [...entries.keys()]) {
    if (!key.startsWith(prefix)) continue;
    // Offline nothing can be refetched, so keep the saved copy and refresh it once back online.
    if (!network.isOnline()) {
      if (entries.get(key)?.data !== undefined) entries.set(key, { ...entries.get(key), stale: true });
      continue;
    }
    const watched = listeners.get(key)?.size;
    if (keep && watched && entries.get(key)?.data !== undefined) {
      load(key, { refresh: true });
      continue;
    }
    entries.delete(key);
    dropped.push(key);
    if (watched) load(key);
  }
  unpersist(dropped);
}

/** Used on sign-out: drop everything silently, including the copy saved on the phone. */
export function invalidateAll() {
  entries.clear();
  inflight.clear();
  AsyncStorage.getAllKeys()
    .then((keys) => AsyncStorage.multiRemove(keys.filter((k) => k.startsWith(STORE_PREFIX))))
    .catch(() => {});
}

// Back online: refresh whatever is on screen and was shown from the saved copy or failed.
network.subscribe((isOnline) => {
  if (!isOnline) return;
  for (const [key, ls] of listeners) {
    const e = entries.get(key);
    if (ls.size && e && (e.stale || e.error)) load(key);
  }
});

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
    // Saved results show at once and refresh quietly in the background (no spinner).
    if (!e || (e.data === undefined && !e.error) || (e.stale && network.isOnline())) load(key);
  }, [key]);

  const refetch = useCallback(() => (key ? load(key, { refresh: true }) : Promise.resolve()), [key]);

  return {
    data: state.data,
    error: state.error,
    loading: !!key && state.data === undefined && !state.error,
    refreshing: state.refreshing,
    stale: state.stale, // showing a saved copy that couldn't be refreshed yet
    refetch,
  };
}
