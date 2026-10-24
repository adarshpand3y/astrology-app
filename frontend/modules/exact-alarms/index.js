// Exact-alarm permission (Android 12+). The native side is in ./android; it is linked into
// development and release builds automatically. Expo Go, iOS and web don't have it, and
// report exact alarms as allowed (there is nothing to ask for there).
import { requireOptionalNativeModule } from 'expo';
import { Platform } from 'react-native';

const native = Platform.OS === 'android' ? requireOptionalNativeModule('ExactAlarms') : null;

/** Whether the "Alarms & reminders" check is available in this build. */
export function exactAlarmsSupported() {
  return !!native;
}

/** True when scheduled notifications can fire on the minute. */
export function canScheduleExactAlarms() {
  try {
    return native ? native.canScheduleExactAlarms() : true;
  } catch {
    return true;
  }
}

/** Opens this app's "Alarms & reminders" settings page; false if there isn't one. */
export async function openExactAlarmSettings() {
  try {
    return native ? await native.openSettingsAsync() : false;
  } catch {
    return false;
  }
}
