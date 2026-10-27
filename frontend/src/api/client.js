import Constants from 'expo-constants';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

import { API_BASE, brand } from '../config/env';
import { network } from '../network';

const ACCESS_KEY = 'auth.access';
const REFRESH_KEY = 'auth.refresh';
const DEFAULT_TIMEOUT_MS = 20000;

export class ApiError extends Error {
  constructor({ status = 0, code = 'error', message = 'Request failed', details = null }) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// --- token store (memory + SecureStore) ---------------------------------------------
let tokens = { access: null, refresh: null };
const logoutListeners = new Set();

export const tokenStore = {
  async load() {
    const [access, refresh] = await Promise.all([
      SecureStore.getItemAsync(ACCESS_KEY), SecureStore.getItemAsync(REFRESH_KEY),
    ]);
    tokens = { access, refresh };
    return tokens;
  },
  get: () => tokens,
  async set({ access, refresh }) {
    tokens = { access: access ?? tokens.access, refresh: refresh ?? tokens.refresh };
    await Promise.all([
      tokens.access ? SecureStore.setItemAsync(ACCESS_KEY, tokens.access) : null,
      tokens.refresh ? SecureStore.setItemAsync(REFRESH_KEY, tokens.refresh) : null,
    ]);
  },
  async clear() {
    tokens = { access: null, refresh: null };
    await Promise.all([SecureStore.deleteItemAsync(ACCESS_KEY), SecureStore.deleteItemAsync(REFRESH_KEY)]);
  },
  onForcedLogout(cb) {
    logoutListeners.add(cb);
    return () => logoutListeners.delete(cb);
  },
};

// --- language (backend localises generated texts) ------------------------------------
let language = 'en';
export function setApiLanguage(lang) { language = lang; }

// --- app version (the server rejects builds older than its minimum) -------------------
export const APP_VERSION = Constants.expoConfig?.version || brand.version;
let updateRequired = null; // { minVersion } once the server has said this build is too old
const updateListeners = new Set();

export const appUpdate = {
  get: () => updateRequired,
  subscribe(cb) {
    updateListeners.add(cb);
    return () => updateListeners.delete(cb);
  },
};

function flagUpdateRequired(details) {
  if (updateRequired) return;
  updateRequired = { minVersion: details?.min_version || null };
  updateListeners.forEach((cb) => cb(updateRequired));
}

// --- low level fetch -----------------------------------------------------------------
function buildUrl(path, query) {
  let url = `${API_BASE}${path}`;
  if (query) {
    const qs = Object.entries(query)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
      .join('&');
    if (qs) url += `?${qs}`;
  }
  return url;
}

async function rawFetch(path, { method = 'GET', body, query, token, timeout = DEFAULT_TIMEOUT_MS }) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const headers = {
    Accept: 'application/json', 'Accept-Language': language, 'X-App-Version': APP_VERSION, 'X-App-Platform': Platform.OS,
  };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Bearer ${token}`;
  try {
    return await fetch(buildUrl(path, query), {
      method, headers, body: body !== undefined ? JSON.stringify(body) : undefined, signal: controller.signal,
    });
  } catch (e) {
    if (e?.name === 'AbortError') throw new ApiError({ code: 'timeout', message: 'timeout' });
    throw new ApiError({ code: 'network_error', message: 'network' });
  } finally {
    clearTimeout(timer);
  }
}

async function parse(res) {
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = null; }
  if (!res.ok) {
    const err = data?.error || {};
    if (res.status === 426 || err.code === 'update_required') flagUpdateRequired(err.details);
    throw new ApiError({
      status: res.status, code: err.code || `http_${res.status}`,
      message: err.message || `HTTP ${res.status}`, details: err.details || null,
    });
  }
  return data;
}

// --- refresh (single flight) -----------------------------------------------------------
let refreshing = null;

async function refreshTokens() {
  if (!tokens.refresh) return false;
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await rawFetch('/auth/token/refresh/', { method: 'POST', body: { refresh: tokens.refresh } });
        if (!res.ok) return false;
        await tokenStore.set(await res.json());
        return true;
      } catch {
        return false;
      } finally {
        setTimeout(() => { refreshing = null; }, 0);
      }
    })();
  }
  return refreshing;
}

/** Authenticated JSON request. Retries once after refreshing an expired access token. */
export async function api(path, { method, body, query, auth = true, timeout } = {}) {
  // Offline the app is read-only: refuse changes before they half-apply.
  if (method && method !== 'GET' && !network.isOnline()) throw new ApiError({ code: 'offline', message: 'offline' });
  const opts = { method, body, query, timeout, token: auth ? tokens.access : null };
  let res = await rawFetch(path, opts);
  if (res.status === 401 && auth && tokens.refresh) {
    if (await refreshTokens()) {
      res = await rawFetch(path, { ...opts, token: tokens.access });
    } else if (!updateRequired) { // a too-old build keeps its session for after the update
      await tokenStore.clear();
      logoutListeners.forEach((cb) => cb());
    }
  }
  return parse(res);
}
