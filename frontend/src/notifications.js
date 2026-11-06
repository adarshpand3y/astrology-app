// Local notifications: the backend computes upcoming alerts (time periods, Rahu Kaal,
// daily insight, dasha changes, transits); the phone schedules them.
//
// expo-notifications is loaded lazily: Expo Go on Android (SDK 53+) no longer ships
// its native module, and a top-level import would crash the app there. In that
// runtime alerts are simply unavailable; a development / store build delivers them.
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

/** Problems worth knowing about while developing; silent in release builds. */
function warn(message) {
  if (__DEV__) console.warn(`[notifications] ${message}`);
}

const errText = (e) => e?.message || String(e);

// --- Times in the phone's own clock ---------------------------------------------------
const pad = (n) => String(n).padStart(2, '0');

/** "15:12" or "3:12 PM" per the phone's 12/24-hour setting, in the phone's timezone. */
function deviceClock(value) {
  const d = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  let h24 = false;
  try { h24 = !!getCalendars()[0]?.uses24hourClock; } catch { /* default to 12-hour */ }
  const h = d.getHours();
  return h24 ? `${pad(h)}:${pad(d.getMinutes())}` : `${h % 12 || 12}:${pad(d.getMinutes())} ${h < 12 ? 'AM' : 'PM'}`;
}

/** Alert text from the server refers to times as {start} / {end}; fill them for this phone. */
function fillTimes(text, times) {
  return (text || '').replace(/\{(\w+)\}/g, (m, key) => (times?.[key] ? deviceClock(times[key]) : m));
}

// --- Native module --------------------------------------------------------------------
let mod; // undefined = not tried yet, null = unavailable

function load() {
  if (mod !== undefined) return mod;
  if (IS_EXPO_GO_ANDROID || Platform.OS === 'web') {
    mod = null;
    warn(`Notifications unavailable in this runtime (${IS_EXPO_GO_ANDROID ? 'Expo Go on Android' : Platform.OS}).`);
    return mod;
  }
  try {
    mod = require('expo-notifications');
    mod.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true, shouldShowList: true, shouldPlaySound: false, shouldSetBadge: false,
      }),
    });
  } catch (e) {
    mod = null;
    warn(`Could not load expo-notifications: ${errText(e)}`);
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
    if (!current.canAskAgain) return false; // denied, and Android won't ask again
    const { status } = await N.requestPermissionsAsync();
    return status === 'granted';
  } catch (e) {
    warn(`Permission request failed: ${errText(e)}`);
    return false;
  }
}

// --- Scheduling -----------------------------------------------------------------------
// Syncs are chained so overlapping calls (launch, focus, settings change) can't interleave
// their cancel + schedule steps and leave duplicates behind.
let syncChain = Promise.resolve();

/** Replace all scheduled alerts with the backend's upcoming feed. */
export function syncSchedule() {
  const run = syncChain.then(doSync, doSync);
  syncChain = run;
  return run;
}

async function doSync() {
  const N = load();
  if (!N) return false;
  try {
    if (!(await notificationsAllowed())) return false;
    const { items } = await alertsApi.schedule(7);
    await ensureChannels(N); // alerts on a missing channel are silently dropped
    const existing = await N.getAllScheduledNotificationsAsync();
    await Promise.all(existing.map((r) => N.cancelScheduledNotificationAsync(r.identifier)));
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
    return true;
  } catch (e) {
    warn(`Sync failed: ${errText(e)}`);
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
  if (!canScheduleExactAlarms()) await promptExactAlarmsOnce(texts);
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
const ROUTES = { period: '/timeline', period_night: '/timeline', rahu: '/timeline', remedy: '/remedies', vrat: '/timeline/calendar' };

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
    if (route) open(route);
    N.clearLastNotificationResponseAsync().catch(() => {}); // don't act on it again next launch
  };
  N.getLastNotificationResponseAsync().then((r) => { if (r) handle(r); }).catch(() => {});
  const sub = N.addNotificationResponseReceivedListener(handle);
  return () => sub.remove();
}
