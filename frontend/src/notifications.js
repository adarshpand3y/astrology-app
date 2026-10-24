// Local notifications: the backend computes upcoming alerts (time periods, Rahu Kaal,
// daily insight, dasha changes, transits); the phone schedules them.
//
// expo-notifications is loaded lazily: Expo Go on Android (SDK 53+) no longer ships
// its native module, and a top-level import would crash the app there. In that
// runtime alerts are simply unavailable; a development / store build delivers them.
//
// Every step is written to an in-memory log so the "Scheduled notifications" screen
// (non-production builds) can show what happened.
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants, { ExecutionEnvironment } from 'expo-constants';
import { getCalendars } from 'expo-localization';
import { Alert, Platform } from 'react-native';

import { canScheduleExactAlarms, openExactAlarmSettings } from '../modules/exact-alarms';
import { alertsApi } from './api/endpoints';

export { canScheduleExactAlarms, openExactAlarmSettings };

const MAX_SCHEDULED = 60; // iOS allows 64 pending local notifications
const IS_EXPO_GO_ANDROID =
  Platform.OS === 'android' && Constants.executionEnvironment === ExecutionEnvironment.StoreClient;

// --- Activity log ---------------------------------------------------------------------
const LOG_MAX = 100;
const log = [];
const listeners = new Set();

function note(level, message) {
  log.unshift({ id: `${Date.now()}-${Math.random()}`, at: Date.now(), level, message });
  if (log.length > LOG_MAX) log.pop();
  listeners.forEach((fn) => fn());
}

/** Newest first: `{ id, at, level: 'info' | 'ok' | 'warn' | 'error', message }`. */
export function getLog() {
  return log.slice();
}

/** Calls `fn` whenever the log changes; returns an unsubscribe function. */
export function subscribeLog(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

const errText = (e) => e?.message || String(e);

// --- Times in the phone's own clock ---------------------------------------------------
const pad = (n) => String(n).padStart(2, '0');

/** "15:12" or "3:12 PM" per the phone's 12/24-hour setting, in the phone's timezone. */
export function deviceClock(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  let h24 = false;
  try { h24 = !!getCalendars()[0]?.uses24hourClock; } catch { /* default to 12-hour */ }
  const h = d.getHours();
  return h24 ? `${pad(h)}:${pad(d.getMinutes())}` : `${h % 12 || 12}:${pad(d.getMinutes())} ${h < 12 ? 'AM' : 'PM'}`;
}

/** Alert text from the server refers to times as {start} / {end}; fill them for this phone. */
export function fillTimes(text, times) {
  return (text || '').replace(/\{(\w+)\}/g, (m, key) => (times?.[key] ? deviceClock(times[key]) : m));
}

// --- Native module --------------------------------------------------------------------
let mod; // undefined = not tried yet, null = unavailable

function load() {
  if (mod !== undefined) return mod;
  if (IS_EXPO_GO_ANDROID || Platform.OS === 'web') {
    mod = null;
    note('warn', `Notifications unavailable in this runtime (${IS_EXPO_GO_ANDROID ? 'Expo Go on Android' : Platform.OS}).`);
    return mod;
  }
  try {
    mod = require('expo-notifications');
    mod.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true, shouldShowList: true, shouldPlaySound: false, shouldSetBadge: false,
      }),
    });
    // Only fires while the app is open; delivery in the background still happens, unlogged.
    mod.addNotificationReceivedListener((n) => note('ok', `Delivered: ${n.request.content.title}`));
    note('info', 'Notification module loaded.');
  } catch (e) {
    mod = null;
    note('error', `Could not load expo-notifications: ${errText(e)}`);
  }
  return mod;
}

/** Whether this runtime can deliver local notifications at all. */
export function notificationsSupported() {
  return !!load();
}

export async function notificationsAllowed() {
  const N = load();
  if (!N) return false;
  try {
    const { status } = await N.getPermissionsAsync();
    return status === 'granted';
  } catch {
    return false;
  }
}

/** Raw permission state for the diagnostics screen. */
export async function permissionDetails() {
  const N = load();
  if (!N) return { supported: false };
  try {
    const p = await N.getPermissionsAsync();
    return { supported: true, status: p.status, canAskAgain: p.canAskAgain };
  } catch (e) {
    return { supported: true, status: 'error', error: errText(e) };
  }
}

// Android channels: time-period alerts get their own so they can be silenced in system
// settings without losing the rest. Night periods use LOW importance: they appear in the
// shade without sound or a pop-up, so they don't wake anyone. Android fixes a channel's
// importance when it's first created, so changing it later needs a new channel id.
const CHANNELS = {
  default: ['Alerts', 'DEFAULT'],
  periods: ['Time periods', 'DEFAULT'],
  periods_night: ['Night time periods', 'LOW'],
};
const CHANNEL_FOR = { period: 'periods', period_night: 'periods_night' };
const channelFor = (category) => CHANNEL_FOR[category] || 'default';

async function ensureChannels(N) {
  if (Platform.OS !== 'android') return;
  for (const [id, [name, importance]] of Object.entries(CHANNELS)) {
    await N.setNotificationChannelAsync(id, { name, importance: N.AndroidImportance[importance] });
  }
}

export async function requestPermission() {
  const N = load();
  if (!N) return false;
  try {
    await ensureChannels(N);
    const current = await N.getPermissionsAsync();
    if (current.status === 'granted') return true;
    if (!current.canAskAgain) {
      note('warn', 'Permission denied and Android won\'t ask again; enable notifications in system settings.');
      return false;
    }
    note('info', 'Asking for notification permission…');
    const { status } = await N.requestPermissionsAsync();
    note(status === 'granted' ? 'ok' : 'warn', `Permission ${status}.`);
    return status === 'granted';
  } catch (e) {
    note('error', `Permission request failed: ${errText(e)}`);
    return false;
  }
}

// --- Scheduling -----------------------------------------------------------------------
// Syncs are chained so overlapping calls (launch, focus, settings change) can't interleave
// their cancel + schedule steps and leave duplicates behind.
let syncChain = Promise.resolve();

/** Replace all scheduled alerts with the backend's upcoming feed (test alerts are kept). */
export function syncSchedule() {
  const run = syncChain.then(doSync, doSync);
  syncChain = run;
  return run;
}

async function doSync() {
  const N = load();
  if (!N) return false;
  try {
    if (!(await notificationsAllowed())) {
      note('warn', 'Sync skipped: notification permission not granted.');
      return false;
    }
    note('info', 'Sync: fetching the alert feed…');
    const { items } = await alertsApi.schedule(7);
    await ensureChannels(N); // alerts on a missing channel are silently dropped
    const existing = await N.getAllScheduledNotificationsAsync();
    const stale = existing.filter((r) => !r.content.data?.test);
    await Promise.all(stale.map((r) => N.cancelScheduledNotificationAsync(r.identifier)));
    const now = Date.now();
    const upcoming = items.filter((i) => Date.parse(i.at) > now + 5000).slice(0, MAX_SCHEDULED);
    for (const item of upcoming) {
      await N.scheduleNotificationAsync({
        content: {
          title: fillTimes(item.title, item.times), body: fillTimes(item.body, item.times),
          data: { category: item.category },
        },
        trigger: { type: N.SchedulableTriggerInputTypes.DATE, date: new Date(item.at), channelId: channelFor(item.category) },
      });
    }
    const counts = {};
    upcoming.forEach((i) => { counts[i.category] = (counts[i.category] || 0) + 1; });
    const summary = Object.entries(counts).map(([k, n]) => `${k} ${n}`).join(', ') || 'nothing upcoming';
    note('ok', `Sync done: feed had ${items.length}, cancelled ${stale.length}, scheduled ${upcoming.length} (${summary}).`);
    return true;
  } catch (e) {
    note('error', `Sync failed: ${errText(e)}`);
    return false;
  }
}

/** Everything the OS currently has queued, soonest first. */
export async function listScheduled() {
  const N = load();
  if (!N) return [];
  const requests = await N.getAllScheduledNotificationsAsync();
  return requests
    .map((r) => {
      const t = r.trigger || {};
      // Android reports a date trigger as { type: 'date', value: ms }; iOS may use `date`.
      const raw = t.value ?? t.date ?? t.timestamp;
      const at = raw == null ? null : new Date(typeof raw === 'number' ? raw : Date.parse(raw));
      return {
        id: r.identifier, title: r.content.title, body: r.content.body, at,
        category: r.content.data?.category || (r.content.data?.test ? 'test' : '?'),
        channel: t.channelId || null,
      };
    })
    .sort((a, b) => (a.at?.getTime() ?? Infinity) - (b.at?.getTime() ?? Infinity));
}

/** Test alert: delivered now (`delaySeconds` 0) or after a delay, through the real scheduler. */
export async function sendTestNotification(delaySeconds = 0) {
  const N = load();
  if (!N) return false;
  if (!(await requestPermission())) return false;
  const at = new Date(Date.now() + delaySeconds * 1000);
  const content = {
    title: delaySeconds ? '🔔 Test alert (scheduled)' : '🔔 Test alert',
    body: delaySeconds
      ? `Scheduled at ${new Date().toLocaleTimeString()} for ${at.toLocaleTimeString()}.`
      : `Sent at ${new Date().toLocaleTimeString()}.`,
    data: { category: 'test', test: true },
  };
  try {
    await N.scheduleNotificationAsync({
      content,
      // null = deliver immediately; a date trigger goes through the same path as real alerts.
      trigger: delaySeconds
        ? { type: N.SchedulableTriggerInputTypes.DATE, date: at, channelId: 'default' }
        : (Platform.OS === 'android' ? { channelId: 'default' } : null),
    });
    note('ok', delaySeconds ? `Test alert scheduled for ${at.toLocaleTimeString()}.` : 'Test alert sent.');
    return true;
  } catch (e) {
    note('error', `Test alert failed: ${errText(e)}`);
    return false;
  }
}

// --- Startup --------------------------------------------------------------------------
const EXACT_PROMPT_KEY = 'notifications.exactPromptShown';

/**
 * Runs once at app start (before sign-in too): asks for notification permission if it isn't
 * granted, then, the first time only, offers the "Alarms & reminders" setting when exact
 * alarms are off. `texts` = { title, message, later, allow }. Resolves to whether
 * notifications are allowed.
 */
export async function setupNotifications(texts) {
  if (!load()) return false;
  const ok = await requestPermission();
  if (!ok) return false;
  const exact = canScheduleExactAlarms();
  note(exact ? 'ok' : 'warn', exact
    ? 'Exact alarms allowed: alerts fire on time.'
    : 'Exact alarms off: Android may hold alerts back, especially while the phone is idle.');
  if (!exact) await promptExactAlarmsOnce(texts);
  return true;
}

async function promptExactAlarmsOnce({ title, message, later, allow }) {
  try {
    if (await AsyncStorage.getItem(EXACT_PROMPT_KEY)) return;
    await AsyncStorage.setItem(EXACT_PROMPT_KEY, '1');
  } catch { /* storage unavailable: ask this time */ }
  Alert.alert(title, message, [
    { text: later, style: 'cancel' },
    { text: allow, onPress: () => { openExactAlarmSettings(); } },
  ]);
}

// --- Opening a notification -----------------------------------------------------------
// Where tapping an alert takes the user, by category; other alerts just open the app.
const ROUTES = { period: '/timeline', period_night: '/timeline', rahu: '/timeline', remedy: '/remedies' };

export function routeForNotification(data) {
  return ROUTES[data?.category] || null;
}

let lastOpened = null; // the same tap can arrive both as the launch response and via the listener

/**
 * Calls `open(route)` when the user taps an alert: the one that launched the app from closed,
 * and any tapped while it runs. Returns an unsubscribe function.
 */
export function onNotificationOpened(open) {
  const N = load();
  if (!N) return () => {};
  const handle = (response) => {
    const { request, date } = response?.notification || {};
    if (!request) return;
    const key = `${request.identifier}:${date}`;
    if (key === lastOpened) return;
    lastOpened = key;
    const route = routeForNotification(request.content.data);
    note('info', `Opened from notification "${request.content.title}"${route ? ` → ${route}` : ''}.`);
    if (route) open(route);
    N.clearLastNotificationResponseAsync().catch(() => {}); // don't act on it again next launch
  };
  N.getLastNotificationResponseAsync().then((r) => { if (r) handle(r); }).catch(() => {});
  const sub = N.addNotificationResponseReceivedListener(handle);
  return () => sub.remove();
}
