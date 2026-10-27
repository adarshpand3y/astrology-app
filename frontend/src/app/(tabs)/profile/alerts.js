import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Alert, Text, View } from 'react-native';

import { alertsApi } from '../../../api/endpoints';
import { AlertToggles } from '../../../components/Preferences';
import { BackLink, Button, ErrorView, Loading, Row, Screen, T } from '../../../components/ui';
import { APP_ENV } from '../../../config/env';
import { invalidate, setCached } from '../../../hooks/useApi';
import { useAlertPrefs, useSchedule } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import {
  canScheduleExactAlarms, deviceClock, fillTimes, notificationsAllowed, notificationsSupported, openExactAlarmSettings,
  requestPermission, syncSchedule,
} from '../../../notifications';
import { useTheme } from '../../../theme';
import { shortDate } from '../../../utils/format';

export default function Alerts() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const prefs = useAlertPrefs();
  const schedule = useSchedule();
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

  const accentFor = (k) => (k === 'bad' ? th.kind.bad.solid : k === 'good' ? th.kind.good.solid : th.c.accent);
  // Same clock as the notifications themselves: the phone's timezone and 12/24-hour setting.
  const when = (iso) => (new Date(iso).toDateString() === new Date().toDateString() ? deviceClock(iso) : `${shortDate(iso, lang)} ${deviceClock(iso)}`);
  const previews = (schedule.data?.items || []).slice(0, 3);

  return (
    <Screen refreshing={prefs.refreshing} onRefresh={() => { prefs.refetch(); schedule.refetch(); }}>
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

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>{t('alerts.preview')}</T>
      <View style={{ gap: 9, marginBottom: 24 }}>
        {schedule.loading ? <Loading style={{ paddingVertical: 20 }} /> : null}
        {!schedule.loading && !previews.length ? <T v="small">{t('alerts.empty')}</T> : null}
        {previews.map((n) => (
          <View key={n.id} style={[{
            backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair, borderRadius: 17, paddingVertical: 12,
            paddingHorizontal: 14, flexDirection: 'row', gap: 11,
          }, th.shadow('card')]}>
            <View style={{ width: 32, height: 32, borderRadius: 9, backgroundColor: accentFor(n.kind), alignItems: 'center', justifyContent: 'center' }}>
              <Text style={{ color: '#fff', fontSize: 15 }}>◈</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Row style={{ justifyContent: 'space-between' }}>
                <T weight={600} style={{ fontSize: 13.5, flex: 1 }} numberOfLines={1}>{fillTimes(n.title, n.times)}</T>
                <T v="tiny" style={{ fontSize: 10.5 }}>{when(n.at)}</T>
              </Row>
              <T v="small" style={{ fontSize: 12, marginTop: 2, lineHeight: 17 }}>{fillTimes(n.body, n.times)}</T>
            </View>
          </View>
        ))}
      </View>

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>{t('alerts.what')}</T>
      <AlertToggles prefs={p} onToggle={toggle} />
      <ErrorView error={schedule.error} style={{ marginTop: 12 }} />
      {APP_ENV !== 'production' ? (
        <Button small variant="secondary" title="Scheduled notifications (debug)" style={{ marginTop: 16 }}
          onPress={() => router.push('/profile/notifications')} />
      ) : null}
    </Screen>
  );
}
