import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';
import Svg, { Circle, Defs, RadialGradient, Stop } from 'react-native-svg';

import { billingApi } from '../api/endpoints';
import { Button, Card, ErrorView, Loading, Row, Screen, T } from '../components/ui';
import { invalidate, setCached } from '../hooks/useApi';
import { useBilling } from '../hooks/data';
import { useI18n } from '../i18n';
import { useTheme } from '../theme';
import { fullDate } from '../utils/format';

const SYMBOL = { INR: '₹', USD: '$', EUR: '€', GBP: '£' };

export default function Paywall() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const { data, error, loading, refetch } = useBilling();
  const [plan, setPlan] = useState('annual');
  const [busy, setBusy] = useState(false);

  if (loading) return <Screen tabs={false}><Loading /></Screen>;
  if (!data) return <Screen tabs={false}><ErrorView error={error} onRetry={refetch} /></Screen>;

  const sym = SYMBOL[data.prices.currency] || `${data.prices.currency} `;
  const money = (n) => `${sym}${Number(n).toLocaleString('en-IN')}`;
  const annual = plan === 'annual';
  const perMonth = Math.round(data.prices.annual / 12);
  const save = Math.round((1 - data.prices.annual / (data.prices.monthly * 12)) * 100);

  const start = async () => {
    if (!data.trial_available) { Alert.alert(t('paywall.comingSoon')); return; }
    setBusy(true);
    try {
      setCached('billing', await billingApi.startTrial());
      // Responses fetched on the free plan are trimmed (D1-only chart, shallow dasha…): refetch them.
      ['p:', 'remedies', 'schedule', 'goals:'].forEach(invalidate);
      Alert.alert(t('paywall.trialStarted'));
      router.back();
    } catch (e) {
      Alert.alert(t('common.unknownError'), e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Screen tabs={false}>
      <Row style={{ justifyContent: 'flex-end', padding: 2 }}>
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ width: 30, height: 30, borderRadius: 15, backgroundColor: th.c.muted, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color: th.c.ink2 }}>✕</Text>
        </Pressable>
      </Row>
      <View style={{ alignItems: 'center', paddingHorizontal: 6, paddingTop: 6, paddingBottom: 22 }}>
        <View style={{ width: 52, height: 52, marginBottom: 14, alignItems: 'center', justifyContent: 'center' }}>
          <Svg width={52} height={52} style={{ position: 'absolute' }}>
            <Defs>
              <RadialGradient id="pw" cx="50%" cy="40%" r="60%">
                <Stop offset="0" stopColor={th.gradient[0]} />
                <Stop offset="1" stopColor={th.gradient[1]} />
              </RadialGradient>
            </Defs>
            <Circle cx={26} cy={26} r={26} fill="url(#pw)" />
          </Svg>
          <Text style={{ fontSize: 22, color: '#fff' }}>◈</Text>
        </View>
        <Text style={[th.font.display(500), { fontSize: 25, lineHeight: 31, color: th.c.ink, textAlign: 'center' }]}>{t('paywall.title')}</Text>
        <T v="small" style={{ fontSize: 13, marginTop: 8, textAlign: 'center', maxWidth: 280 }}>{t('paywall.sub')}</T>
      </View>

      {data.is_pro ? (
        <Card radius={20} pad={20} border={th.c.accent} style={{ alignItems: 'center', marginBottom: 16 }}>
          <Text style={[th.font.display(500), { fontSize: 22, color: th.c.ink }]}>{t('paywall.active')}</Text>
          {data.on_trial ? <T v="small" style={{ marginTop: 4 }}>{t('paywall.activeUntil', { date: fullDate(data.trial_ends_at, lang) })}</T> : null}
        </Card>
      ) : (
        <>
          <View style={{ flexDirection: 'row', gap: 4, backgroundColor: th.c.muted, borderRadius: 14, padding: 4, marginBottom: 16 }}>
            {['monthly', 'annual'].map((p) => (
              <Pressable key={p} onPress={() => setPlan(p)} style={{
                flex: 1, alignItems: 'center', paddingVertical: 11, paddingHorizontal: 8, borderRadius: 11,
                backgroundColor: plan === p ? th.c.accent : 'transparent',
              }}>
                <Text style={[th.font.ui(600), { fontSize: 13, color: plan === p ? th.c.onAccent : th.c.ink2 }]}>{t(`paywall.${p}`)}</Text>
              </Pressable>
            ))}
          </View>
          <Card radius={20} pad={20} border={th.c.accent} style={[{ borderWidth: 1.5, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: 18 }, th.shadow('cta')]}>
            <View>
              <Text style={[th.font.display(500), { fontSize: 30, color: th.c.ink }]}>
                {money(annual ? data.prices.annual : data.prices.monthly)}
                <Text style={{ fontSize: 15, color: th.c.ink3 }}>{t(annual ? 'paywall.perYear' : 'paywall.perMonth')}</Text>
              </Text>
              <T v="caption" style={{ fontSize: 12, color: th.c.accentDark, marginTop: 2 }}>
                {annual ? t('paywall.annualNote', { m: money(perMonth), p: save }) : t('paywall.monthlyNote')}
              </T>
            </View>
            {data.trial_available ? (
              <View style={{ paddingVertical: 6, paddingHorizontal: 11, borderRadius: 20, backgroundColor: th.soft(0.15) }}>
                <Text style={[th.font.ui(700), { fontSize: 11, color: th.c.accentDark }]}>{t('paywall.trial', { n: data.trial_days })}</Text>
              </View>
            ) : null}
          </Card>
        </>
      )}

      <Row style={{ marginTop: 20, marginBottom: 8, paddingHorizontal: 4 }}>
        <View style={{ flex: 1 }} />
        <Text style={[th.font.ui(700), { width: 48, textAlign: 'center', fontSize: 10, letterSpacing: 0.5, textTransform: 'uppercase', color: th.c.ink3 }]}>{t('paywall.free')}</Text>
        <Text style={[th.font.ui(700), { width: 48, textAlign: 'center', fontSize: 10, letterSpacing: 0.5, textTransform: 'uppercase', color: th.c.accent }]}>{t('paywall.pro')}</Text>
      </Row>
      <View style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair, borderRadius: 18, overflow: 'hidden' }}>
        {data.features.map((f, i) => (
          <Row key={f.key} gap={0} style={{ paddingVertical: 12, paddingHorizontal: 16, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
            <T style={{ flex: 1, fontSize: 13 }}>{t(`paywall.features.${f.key}`)}</T>
            <Text style={{ width: 48, textAlign: 'center', color: th.c.ink3, fontSize: 14 }}>{f.free ? '✓' : '—'}</Text>
            <Text style={{ width: 48, textAlign: 'center', color: th.c.accent, fontSize: 15 }}>✓</Text>
          </Row>
        ))}
      </View>

      {!data.is_pro ? (
        <>
          <Button title={data.trial_available ? t('paywall.startTrial') : t('paywall.comingSoon')} onPress={start} loading={busy}
            disabled={!data.trial_available} style={{ marginTop: 18, paddingVertical: 16 }} />
          {!data.trial_available ? <T v="tiny" style={{ textAlign: 'center', marginTop: 8 }}>{t('paywall.trialUsed')}</T> : null}
          <Row gap={0} style={{ justifyContent: 'center', marginTop: 14 }}>
            <T v="small" style={{ fontSize: 12 }}>{t('paywall.oneOff')}</T>
            <Text onPress={() => Alert.alert(t('paywall.comingSoon'))} style={[th.font.ui(600), { fontSize: 12, color: th.c.accent }]}>{t('paywall.oneOffLink')}</Text>
          </Row>
        </>
      ) : null}
      <T v="tiny" style={{ textAlign: 'center', marginTop: 10 }}>{t('paywall.footer')}</T>
    </Screen>
  );
}
