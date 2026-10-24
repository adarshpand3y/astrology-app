// Notification diagnostics (non-production builds only): permission state, what the OS has
// queued, the scheduler's activity log, and buttons to fire test alerts. English only.
import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useState } from 'react';
import { Linking, View } from 'react-native';

import { BackLink, Button, Card, Row, Screen, T } from '../../../components/ui';
import { API_URL, APP_ENV } from '../../../config/env';
import {
  canScheduleExactAlarms, getLog, listScheduled, openExactAlarmSettings, permissionDetails, sendTestNotification,
  subscribeLog, syncSchedule,
} from '../../../notifications';
import { useTheme } from '../../../theme';

const stamp = (d) => (d ? `${d.toDateString().slice(0, 10)}  ${d.toTimeString().slice(0, 8)}` : 'no time');
const time = (ms) => new Date(ms).toTimeString().slice(0, 8);

export default function NotificationDiagnostics() {
  const th = useTheme();
  const [log, setLog] = useState(getLog);
  const [scheduled, setScheduled] = useState([]);
  const [perm, setPerm] = useState(null);
  const [exact, setExact] = useState(true);
  const [busy, setBusy] = useState(null);

  const refresh = useCallback(async () => {
    setPerm(await permissionDetails());
    setExact(canScheduleExactAlarms());
    try { setScheduled(await listScheduled()); } catch { setScheduled([]); }
  }, []);

  useFocusEffect(useCallback(() => { refresh(); }, [refresh]));
  // The log changes after every sync / test, which is also when the queue changes.
  useEffect(() => subscribeLog(() => { setLog(getLog()); refresh(); }), [refresh]);

  const run = (key, fn) => async () => {
    setBusy(key);
    try { await fn(); } finally { setBusy(null); refresh(); }
  };

  const levelColor = { ok: th.kind.good.solid, warn: th.kind.neutral.solid, error: th.kind.bad.solid, info: th.c.ink3 };
  const granted = perm?.status === 'granted';

  return (
    <Screen onRefresh={refresh} refreshing={false}>
      <BackLink label="Alerts" />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 4 }}>Scheduled notifications</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 14 }}>Debug view · {APP_ENV} build · {API_URL}</T>

      <Card style={{ marginBottom: 14 }}>
        <Row style={{ justifyContent: 'space-between' }}>
          <T weight={600}>Permission</T>
          <T weight={600} style={{ color: granted ? th.kind.good.solid : th.kind.bad.solid }}>
            {!perm ? '…' : perm.supported === false ? 'unsupported' : perm.status}
          </T>
        </Row>
        {perm && perm.supported !== false && !granted ? (
          <T v="caption" style={{ marginTop: 6 }}>
            {perm.canAskAgain ? 'Tap "Send now" to be asked.' : 'Android will not ask again.'}{' '}
            <T v="caption" style={{ color: th.c.accent }} onPress={() => Linking.openSettings()}>Open app settings</T>
          </T>
        ) : null}
        <Row style={{ justifyContent: 'space-between', marginTop: 12 }}>
          <T weight={600}>Exact alarms</T>
          <T weight={600} style={{ color: exact ? th.kind.good.solid : th.kind.bad.solid }}>{exact ? 'allowed' : 'off'}</T>
        </Row>
        <T v="caption" style={{ marginTop: 6 }}>
          {exact
            ? 'Scheduled alerts fire on the minute, 15 minutes before each event (the daily insight at its set time).'
            : 'Android may hold scheduled alerts back, by up to an hour while the phone is idle. '}
          {!exact ? (
            <T v="caption" style={{ color: th.c.accent }} onPress={openExactAlarmSettings}>Allow &quot;Alarms &amp; reminders&quot;</T>
          ) : null}
        </T>
        {!exact ? (
          <T v="caption" style={{ marginTop: 6 }}>After allowing it, come back and tap &quot;Sync now&quot; (the app also re-syncs by itself).</T>
        ) : null}
      </Card>

      <Row gap={8} style={{ marginBottom: 8 }}>
        <Button small style={{ flex: 1 }} title="Send now" loading={busy === 'now'} onPress={run('now', () => sendTestNotification(0))} />
        <Button small style={{ flex: 1 }} title="In 1 minute" loading={busy === 'min'} onPress={run('min', () => sendTestNotification(60))} />
      </Row>
      <Button small variant="secondary" title="Sync now from server" loading={busy === 'sync'} onPress={run('sync', syncSchedule)} style={{ marginBottom: 6 }} />
      <T v="caption" style={{ marginBottom: 20, paddingHorizontal: 2 }}>
        &quot;In 1 minute&quot; goes through the same scheduler as real alerts; close the app to check background delivery.
      </T>

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>Queued on this phone ({scheduled.length})</T>
      <Card pad={0} style={{ marginBottom: 20 }}>
        {!scheduled.length ? <T v="small" style={{ padding: 14 }}>Nothing is scheduled.</T> : null}
        {scheduled.map((n, i) => (
          <View key={n.id} style={{ paddingVertical: 10, paddingHorizontal: 14, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
            <Row style={{ justifyContent: 'space-between' }}>
              <T v="mono" style={{ fontSize: 11 }}>{stamp(n.at)}</T>
              <T v="tiny" style={{ fontSize: 10 }}>{n.category}{n.channel ? ` · ${n.channel}` : ''}</T>
            </Row>
            <T weight={600} style={{ fontSize: 13, marginTop: 3 }}>{n.title}</T>
            <T v="caption" style={{ marginTop: 1 }}>{n.body}</T>
          </View>
        ))}
      </Card>

      <T v="eyebrow" style={{ marginHorizontal: 2, marginBottom: 10 }}>Activity (this session)</T>
      <Card pad={0}>
        {!log.length ? <T v="small" style={{ padding: 14 }}>No activity yet.</T> : null}
        {log.map((e, i) => (
          <Row key={e.id} align="flex-start" gap={10} style={{ paddingVertical: 8, paddingHorizontal: 14, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
            <T v="mono" style={{ fontSize: 10.5, color: th.c.ink3, marginTop: 1 }}>{time(e.at)}</T>
            <T v="caption" style={{ flex: 1, color: levelColor[e.level] || th.c.ink2 }}>{e.message}</T>
          </Row>
        ))}
      </Card>
    </Screen>
  );
}
