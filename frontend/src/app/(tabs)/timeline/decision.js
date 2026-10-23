import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';

import { dailyApi } from '../../../api/endpoints';
import { TimelineNav } from '../../../components/TimelineNav';
import { Button, Chip, ErrorView, FadeIn, ProLock, Row, Screen, Seg, T } from '../../../components/ui';
import { useBilling } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { dayAndTime } from '../../../utils/format';

const ACTIVITIES = [['travel', '✈'], ['purchase', '◈'], ['contract', '✎'], ['venture', '❋'], ['medical', '✚']];
const RANGES = ['today', 'week', 'month'];

function ScoreRing({ score, color }) {
  const th = useTheme();
  const c = 2 * Math.PI * 20;
  return (
    <View style={{ width: 46, height: 46, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={46} height={46} viewBox="0 0 46 46" style={{ position: 'absolute' }}>
        <Circle cx={23} cy={23} r={20} fill="none" stroke={th.c.track} strokeWidth={4} />
        <Circle cx={23} cy={23} r={20} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={`${(score / 100) * c} ${c}`} transform="rotate(-90 23 23)" />
      </Svg>
      <Text style={[th.font.ui(700), { fontSize: 14, color }]}>{score}</Text>
    </View>
  );
}

export default function Decision() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const billing = useBilling();
  const [activity, setActivity] = useState('travel');
  const [rangeKey, setRangeKey] = useState('week');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const isPro = billing.data?.is_pro;

  const find = async () => {
    if (billing.data && !isPro) {
      router.push('/paywall');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setResult(await dailyApi.decision(activity, rangeKey));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen>
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingTop: 8, paddingBottom: 3 }}>{t('decision.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 16 }}>{t('decision.sub')}</T>
      <TimelineNav current="decision" />

      <T v="label" style={{ marginBottom: 9 }}>{t('decision.activity')}</T>
      <Row gap={9} style={{ flexWrap: 'wrap', marginBottom: 22 }}>
        {ACTIVITIES.map(([k, g]) => (
          <Chip key={k} glyph={g} label={t(`decision.activities.${k}`)} active={activity === k}
            onPress={() => { setActivity(k); setResult(null); }} />
        ))}
      </Row>
      <T v="label" style={{ marginBottom: 9 }}>{t('decision.window')}</T>
      <Seg options={RANGES.map((r) => ({ value: r, label: t(`decision.ranges.${r}`) }))} value={rangeKey}
        onChange={(v) => { setRangeKey(v); setResult(null); }} style={{ marginBottom: 22 }} />

      <Button title={t('decision.find')} onPress={find} loading={busy} />
      {error?.code === 'pro_required' ? <ProLock text={t('paywall.sub')} /> : <ErrorView error={error} style={{ marginTop: 14 }} />}

      {result ? (
        <FadeIn style={{ marginTop: 26 }}>
          <Row style={{ justifyContent: 'space-between', marginBottom: 12 }}>
            <T v="section">{t('decision.ranked')}</T>
            <T v="mono" style={{ fontSize: 10, textTransform: 'uppercase' }}>
              {result.activity.object} · {result.range_label}
            </T>
          </Row>
          {!result.results.length ? <T v="small">{t('decision.empty')}</T> : null}
          {result.results.map((r) => {
            const k = th.kind[r.kind];
            const dt = dayAndTime(r.start, lang);
            return (
              <Row key={r.start} gap={14} style={{ backgroundColor: k.tint, borderRadius: 16, padding: 14, marginBottom: 9 }}>
                <ScoreRing score={r.score} color={k.solid} />
                <View style={{ flex: 1 }}>
                  <Row gap={8} align="baseline">
                    <T weight={600} style={{ fontSize: 14.5 }}>{dt.day}</T>
                    <T v="mono" style={{ fontSize: 12, color: k.solid }}>{dt.time}</T>
                  </Row>
                  <T v="caption" style={{ marginTop: 3 }}>{r.reason}</T>
                </View>
              </Row>
            );
          })}
        </FadeIn>
      ) : null}
    </Screen>
  );
}
