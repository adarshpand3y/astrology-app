import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, Text, View } from 'react-native';

import { alertsApi } from '../../../api/endpoints';
import { BackLink, ErrorView, Loading, Row, Screen, Switch, T } from '../../../components/ui';
import { invalidate, setCached } from '../../../hooks/useApi';
import { useAlertPrefs, useSchedule } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { notificationsAllowed, notificationsSupported, requestPermission, syncSchedule } from '../../../notifications';
import { useTheme } from '../../../theme';
import { clock, shortDate, todayISO } from '../../../utils/format';

const FIELDS = ['dasha', 'transit', 'rahu', 'sade_sati', 'daily', 'periods'];

export default function Alerts() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const prefs = useAlertPrefs();
  const schedule = useSchedule();
  const [allowed, setAllowed] = useState(true);

  useEffect(() => { notificationsAllowed().then(setAllowed); }, []);

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

  const sub = (field) => {
    if (field === 'rahu') return t('alerts.rahuSub', { n: p.rahu_lead_minutes });
    if (field === 'daily') {
      const [h, m] = p.daily_time.split(':');
      return t('alerts.dailySub', { t: clock(`2000-01-01T${h}:${m}`, lang, true) });
    }
    return t(`alerts.${field}Sub`);
  };

  const accentFor = (k) => (k === 'bad' ? th.kind.bad.solid : k === 'good' ? th.kind.good.solid : th.c.accent);
  const when = (iso) => (iso.slice(0, 10) === todayISO() ? clock(iso, lang, true) : `${shortDate(iso, lang)} ${clock(iso, lang, true)}`);
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
                <T weight={600} style={{ fontSize: 13.5, flex: 1 }} numberOfLines={1}>{n.title}</T>
                <T v="tiny" style={{ fontSize: 10.5 }}>{when(n.at)}</T>
              </Row>
              <T v="small" style={{ fontSize: 12, marginTop: 2, lineHeight: 17 }}>{n.body}</T>
            </View>
          </View>
        ))}
      </View>

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>{t('alerts.what')}</T>
      <View style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair, borderRadius: 18, overflow: 'hidden' }}>
        {FIELDS.map((f, i) => (
          <Row key={f} gap={13} style={{ paddingVertical: 14, paddingHorizontal: 16, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
            <View style={{ flex: 1 }}>
              <T weight={600} style={{ fontSize: 14 }}>
                {t(`alerts.${f}`)}{p.pro_fields.includes(f) && !p.is_pro ? <Text style={{ color: th.c.accent, fontSize: 11 }}>  ◆ {t('common.pro')}</Text> : null}
              </T>
              <T v="caption" style={{ marginTop: 1 }}>{sub(f)}</T>
            </View>
            <Switch value={!!p[f]} onChange={() => toggle(f)} />
          </Row>
        ))}
      </View>
      <ErrorView error={schedule.error} style={{ marginTop: 12 }} />
    </Screen>
  );
}
