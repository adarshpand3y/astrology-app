import { Tabs } from 'expo-router';
import { useEffect } from 'react';
import { AppState } from 'react-native';

import { TabBar } from '../../components/TabBar';
import { brand } from '../../config/env';
import { useAccount } from '../../hooks/data';
import { useI18n } from '../../i18n';
import { requestPermission, syncSchedule } from '../../notifications';
import { useTheme } from '../../theme';

const HIDDEN = new Set(brand.features.remedies ? [] : ['remedies']);
const RESYNC_MS = 6 * 60 * 60 * 1000;

export default function TabsLayout() {
  const theme = useTheme();
  const { lang } = useI18n();
  const { profileId, placeId } = useAccount();

  // Alerts are on by default, so ask for notification permission (Android 13+ / iOS) once the
  // user reaches the app instead of waiting for them to flip a switch; nothing schedules without it.
  useEffect(() => { requestPermission().then((ok) => { if (ok) syncSchedule(); }); }, []);

  // Keep scheduled local alerts in step with the active chart, place and language.
  useEffect(() => { syncSchedule(); }, [profileId, placeId, lang]);

  // The schedule only covers the next few days (period alerts fill the phone's ~60 slots), so
  // top it up when the app comes back to the foreground, at most every few hours.
  useEffect(() => {
    let last = Date.now();
    const sub = AppState.addEventListener('change', (state) => {
      if (state !== 'active' || Date.now() - last < RESYNC_MS) return;
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
