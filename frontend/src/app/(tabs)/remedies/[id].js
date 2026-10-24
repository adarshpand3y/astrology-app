import * as Haptics from 'expo-haptics';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { remediesApi } from '../../../api/endpoints';
import { RemedyIcon } from '../../../components/Icons';
import { BackLink, Button, Card, ErrorView, Loading, Row, Screen, T, TextLink } from '../../../components/ui';
import { useRemedies } from '../../../hooks/data';
import { invalidate, setCached, useApi } from '../../../hooks/useApi';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { DAY_LETTERS, todayISO } from '../../../utils/format';

function Ring({ value, target, onPress }) {
  const th = useTheme();
  const { t } = useI18n();
  const c = 2 * Math.PI * 66;
  const frac = Math.min(1, target ? value / target : 0);
  return (
    <Pressable onPress={onPress} style={{ width: 150, height: 150, alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
      <Svg width={150} height={150} viewBox="0 0 150 150" style={{ position: 'absolute' }}>
        <Circle cx={75} cy={75} r={66} fill="none" stroke={th.c.track} strokeWidth={10} />
        <Circle cx={75} cy={75} r={66} fill="none" stroke={th.c.accent} strokeWidth={10} strokeLinecap="round"
          strokeDasharray={`${frac * c} ${c}`} transform="rotate(-90 75 75)" />
      </Svg>
      <Text style={[th.font.display(500), { fontSize: 34, color: th.c.accent }]}>{value}</Text>
      <T v="tiny">{t('remedies.ofToday', { n: target })}</T>
    </Pressable>
  );
}

export default function RemedyDetail() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const key = `remedy:${id}:${lang}`;
  const { data, error, loading, refetch } = useApi(key, () => remediesApi.get(id, todayISO()));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const locked = useRemedies().data?.locked; // editing is Pro

  if (loading) return <Screen><Loading /></Screen>;
  if (!data) return <Screen><ErrorView error={error} onRetry={refetch} /></Screen>;

  const send = async (body) => {
    setErr(null);
    try {
      const r = await remediesApi.progress(id, { ...body, today: todayISO() });
      setCached(key, r.remedy);
      invalidate('remedies:');
      invalidate('remedy-history:');
      return r;
    } catch (e) {
      if (e.code === 'pro_required') router.push('/paywall');
      else setErr(e);
      return null;
    }
  };

  const tap = async () => {
    if (data.today.completed) return;
    Haptics.selectionAsync().catch(() => {});
    setCached(key, { ...data, today: { ...data.today, count: data.today.count + 1 } });
    await send({ increment: 1 });
  };

  const complete = async () => {
    setBusy(true);
    await send({ completed: true });
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    setBusy(false);
  };

  const isCounter = data.target > 1;
  return (
    <Screen>
      <Row style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <BackLink label={t('remedies.title')} />
        <TextLink title={locked ? `◆ ${t('remedies.edit')}` : t('remedies.edit')}
          onPress={() => router.push(locked ? '/paywall' : `/remedies/edit/${id}`)} />
      </Row>
      <View style={{ alignItems: 'center' }}>
        {isCounter ? <Ring value={data.today.count} target={data.target} onPress={tap} /> : (
          <View style={{ width: 96, height: 96, borderRadius: 48, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
            <RemedyIcon kind={data.kind} size={44} color={th.c.accent} />
          </View>
        )}
        <Text style={[th.font.display(400), { fontSize: 22, color: th.c.ink, textAlign: 'center' }]}>{data.title}</Text>
        <T v="small" style={{ fontSize: 13, marginTop: 3, textAlign: 'center' }}>{data.text || data.cadence}</T>
        {data.basis_label ? (
          <T v="caption" style={{ marginTop: 4, textAlign: 'center', color: th.c.accentDark }}>{data.basis_label}</T>
        ) : null}
        {isCounter && !data.today.completed ? <T v="tiny" style={{ marginTop: 6 }}>{t('remedies.tapCount')}</T> : null}
      </View>

      {data.how ? (
        <Card radius={18} pad={18} style={{ marginTop: 20, paddingVertical: 16 }}>
          <T v="eyebrow" style={{ marginBottom: 10 }}>{t('remedies.howWhy')}</T>
          <T v="small" style={{ fontSize: 13, lineHeight: 21, color: th.c.ink2 }}>{data.how}</T>
        </Card>
      ) : null}

      <Row gap={6} style={{ marginTop: 16 }}>
        {data.week.map((d, i) => (
          <View key={d.date} style={{
            flex: 1, height: 34, borderRadius: 9, alignItems: 'center', justifyContent: 'center',
            backgroundColor: d.done ? th.c.accent : th.c.muted,
          }}>
            <Text style={[th.font.ui(600), { fontSize: 11, color: d.done ? th.c.onAccent : th.c.ink3 }]}>{DAY_LETTERS[lang][i]}</Text>
          </View>
        ))}
      </Row>
      <ErrorView error={err} style={{ marginTop: 12 }} />
      <Button
        title={data.today.completed ? t('remedies.doneToday') : data.due_today ? t('remedies.markDone') : t('remedies.notDue')}
        disabled={data.today.completed || !data.due_today}
        loading={busy}
        onPress={complete}
        style={{ marginTop: 18 }}
      />
    </Screen>
  );
}
