import { Tabs, useRouter } from 'expo-router';
import { useEffect } from 'react';
import { AppState } from 'react-native';

import { TabBar } from '../../components/TabBar';
import { brand } from '../../config/env';
import { useAccount } from '../../hooks/data';
import { useI18n } from '../../i18n';
import { canScheduleExactAlarms, onNotificationOpened, syncSchedule } from '../../notifications';
import { useTheme } from '../../theme';

const HIDDEN = new Set(brand.features.remedies ? [] : ['remedies']);
const RESYNC_MS = 30 * 60 * 1000; // re-sync when the app is reopened, but not on every quick switch

export default function TabsLayout() {
  const theme = useTheme();
  const { lang } = useI18n();
  const { profileId, placeId } = useAccount();
  const router = useRouter();

  // Tapping an alert opens its screen: time periods and Rahu Kaal -> Timeline, remedy reminder ->
  // Remedies. Handled here because the tabs only exist once signed in; a tap made while signed
  // out is picked up after sign-in.
  useEffect(() => onNotificationOpened((route) => router.navigate(route)), [router]);

  // Notification permission is asked at app start (root layout). Keep scheduled local alerts in
  // step with the active chart, place and language.
  useEffect(() => { syncSchedule(); }, [profileId, placeId, lang]);

  // The schedule only covers the next few days (period alerts fill the phone's ~60 slots), so
  // top it up when the app comes back to the foreground (at most every 30 minutes). Also re-sync
  // right away when exact alarms were just allowed (e.g. back from "Alarms & reminders"):
  // alerts already queued were scheduled inexact and need scheduling again to fire on time.
  useEffect(() => {
    let last = Date.now();
    let exact = canScheduleExactAlarms();
    const sub = AppState.addEventListener('change', (state) => {
      if (state !== 'active') return;
      const nowExact = canScheduleExactAlarms();
      const gained = nowExact && !exact;
      exact = nowExact;
      if (!gained && Date.now() - last < RESYNC_MS) return;
      last = Date.now();
      syncSchedule();
    });
    return () => sub.remove();
  }, []);

  return (
    <Tabs
      tabBar={(props) => <TabBar {...props} hidden={HIDDEN} />}
      screenOptions={{ headerShown: false, sceneStyle: { backgroundColor: theme.c.bg } }}
    >
      <Tabs.Screen name="index" />
      <Tabs.Screen name="timeline" />
      <Tabs.Screen name="chart" />
      <Tabs.Screen name="remedies" />
      <Tabs.Screen name="profile" />
    </Tabs>
  );
}
