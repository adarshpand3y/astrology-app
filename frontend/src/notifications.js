// Local notifications: the backend computes upcoming alerts (time periods, Rahu Kaal,
// daily insight, dasha changes, transits); the phone schedules them.
//
// expo-notifications is loaded lazily: Expo Go on Android (SDK 53+) no longer ships
// its native module, and a top-level import would crash the app there. In that
// runtime alerts are simply unavailable; a development / store build delivers them.
import Constants, { ExecutionEnvironment } from 'expo-constants';
import { Platform } from 'react-native';

import { alertsApi } from './api/endpoints';

const MAX_SCHEDULED = 60; // iOS allows 64 pending local notifications
const IS_EXPO_GO_ANDROID =
  Platform.OS === 'android' && Constants.executionEnvironment === ExecutionEnvironment.StoreClient;

let mod; // undefined = not tried yet, null = unavailable

function load() {
  if (mod !== undefined) return mod;
  if (IS_EXPO_GO_ANDROID || Platform.OS === 'web') {
    mod = null;
    return mod;
  }
  try {
    mod = require('expo-notifications');
    mod.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true, shouldShowList: true, shouldPlaySound: false, shouldSetBadge: false,
      }),
    });
  } catch {
    mod = null;
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
// settings without losing the rest. Creating a channel again is a no-op.
const CHANNELS = { default: 'Alerts', periods: 'Time periods' };
const channelFor = (category) => (category === 'period' ? 'periods' : 'default');

async function ensureChannels(N) {
  if (Platform.OS !== 'android') return;
  for (const [id, name] of Object.entries(CHANNELS)) {
    await N.setNotificationChannelAsync(id, { name, importance: N.AndroidImportance.DEFAULT });
  }
}

export async function requestPermission() {
  const N = load();
  if (!N) return false;
  try {
    await ensureChannels(N);
    const current = await N.getPermissionsAsync();
    if (current.status === 'granted') return true;
    if (!current.canAskAgain) return false;
    const { status } = await N.requestPermissionsAsync();
    return status === 'granted';
  } catch {
    return false;
  }
}

/** Replace all scheduled alerts with the backend's upcoming feed. */
export async function syncSchedule() {
  const N = load();
  if (!N) return false;
  try {
    if (!(await notificationsAllowed())) return false;
    const { items } = await alertsApi.schedule(7);
    await ensureChannels(N); // alerts on a missing channel are silently dropped
    await N.cancelAllScheduledNotificationsAsync();
    const now = Date.now();
    const upcoming = items.filter((i) => Date.parse(i.at) > now + 5000).slice(0, MAX_SCHEDULED);
    for (const item of upcoming) {
      await N.scheduleNotificationAsync({
        content: { title: item.title, body: item.body, data: { category: item.category } },
        trigger: { type: N.SchedulableTriggerInputTypes.DATE, date: new Date(item.at), channelId: channelFor(item.category) },
      });
    }
    return true;
  } catch {
    return false;
  }
}
