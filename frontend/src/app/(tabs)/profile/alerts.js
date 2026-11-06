import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Alert, View } from 'react-native';

import { alertsApi } from '../../../api/endpoints';
import { AlertToggles } from '../../../components/Preferences';
import { BackLink, Button, ErrorView, Loading, Screen, T } from '../../../components/ui';
import { invalidate, setCached } from '../../../hooks/useApi';
import { useAlertPrefs } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import {
  canScheduleExactAlarms, notificationsAllowed, notificationsSupported, openExactAlarmSettings, requestPermission,
  syncSchedule,
} from '../../../notifications';
import { useTheme } from '../../../theme';

export default function Alerts() {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const prefs = useAlertPrefs();
  const [allowed, setAllowed] = useState(true);
  const [exact, setExact] = useState(true);

  useEffect(() => { notificationsAllowed().then(setAllowed); }, []);
  // Re-check on focus: the user may have just come back from the "Alarms & reminders" page.
  useFocusEffect(useCallback(() => { setExact(canScheduleExactAlarms()); }, []));

  if (prefs.loading) return <Screen><Loading /></Screen>;
  if (!prefs.data) return <Screen><ErrorView error={prefs.error} onRetry={prefs.refetch} /></Screen>;
  const p = prefs.data;

  const toggle = async (field) => {
    const next = !p[field];
    if (next && p.pro_fields.includes(field) && !p.is_pro) { router.push('/paywall'); return; }
    if (next) setAllowed(await requestPermission());
    setCached('alert-prefs', { ...p, [field]: next });
    try {
      setCached('alert-prefs', await alertsApi.update({ [field]: next }));
      invalidate('schedule:');
      syncSchedule();
    } catch (e) {
      setCached('alert-prefs', p);
      Alert.alert(t('common.unknownError'), e.message);
    }
  };

  return (
    <Screen refreshing={prefs.refreshing} onRefresh={prefs.refetch}>
      <BackLink label={t('tabs.profile')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 14 }}>{t('alerts.title')}</T>
      {!allowed ? (
        <View style={{ backgroundColor: th.kind.neutral.tint, borderRadius: 13, padding: 13, marginBottom: 14 }}>
          <T v="small">{notificationsSupported() ? t('alerts.permission') : t('alerts.unsupported')}</T>
        </View>
      ) : null}
      {allowed && !exact ? (
        <View style={{ backgroundColor: th.kind.neutral.tint, borderRadius: 13, padding: 13, marginBottom: 14, gap: 10 }}>
          <T v="small">{t('alerts.exactOff')}</T>
          <Button small title={t('alerts.exactFix')} onPress={openExactAlarmSettings} />
        </View>
      ) : null}

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>{t('alerts.what')}</T>
      <AlertToggles prefs={p} onToggle={toggle} />
    </Screen>
  );
}
