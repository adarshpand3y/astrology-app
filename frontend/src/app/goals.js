import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { remediesApi } from '../api/endpoints';
import { GoalPicker } from '../components/GoalPicker';
import { Button, ErrorView, Loading, Row, Screen, T, TextLink } from '../components/ui';
import { useGoals } from '../hooks/data';
import { invalidate } from '../hooks/useApi';
import { useI18n } from '../i18n';
import { useAuth } from '../state/AuthContext';
import { useTheme } from '../theme';
import { todayISO } from '../utils/format';

/** Modal: change goals later (remedies for new goals are added; untouched ones for dropped goals go). */
export default function Goals() {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const { data, error, loading, refetch } = useGoals();
  const [picked, setPicked] = useState(null);
  const [hint, setHint] = useState(null);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const max = data?.max || 1;
  // A free user who picked several goals while on Pro keeps them until they save again.
  const goals = picked ?? data?.goals ?? [];

  const save = async () => {
    if (!goals.length) { setHint(t('onboarding.goalsPick')); return; }
    if (goals.length > max) { setHint(t('onboarding.goalsMax', { n: max })); return; }
    setBusy(true);
    setSaveError(null);
    try {
      await remediesApi.setGoals(goals, todayISO());
      invalidate('goals:');
      invalidate('remedies:');
      invalidate('remedy-history:');
      await refreshUser();
      router.back();
    } catch (e) {
      setBusy(false);
      if (e.code === 'pro_required') router.push('/paywall');
      else setSaveError(e);
    }
  };

  return (
    <Screen tabs={false}>
      <Row style={{ justifyContent: 'space-between', paddingTop: 6, paddingBottom: 6 }}>
        <T v="screenTitle">{t('goals.title')}</T>
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ width: 30, height: 30, borderRadius: 15, backgroundColor: th.c.muted, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color: th.c.ink2 }}>✕</Text>
        </Pressable>
      </Row>
      <T v="small" style={{ marginBottom: 16 }}>{t('goals.sub')}</T>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <>
          {max > 1 ? <T v="caption" style={{ marginBottom: 10 }}>{t('goals.count', { n: goals.length, max })}</T> : null}
          <GoalPicker catalogue={data.catalogue} value={goals} max={max}
            onChange={(v) => { setPicked(v); setHint(null); }}
            onLimit={() => setHint(t('onboarding.goalsMax', { n: max }))} />
        </>
      ) : null}
      {hint ? <T v="caption" style={{ color: th.kind.bad.solid, marginTop: 12, textAlign: 'center' }}>{hint}</T> : null}
      {data && !data.is_pro ? (
        <View style={{ alignItems: 'center', marginTop: 14, gap: 6 }}>
          <T v="caption" style={{ textAlign: 'center' }}>{t('goals.freeNote', { n: data.pro_max })}</T>
          <TextLink title={t('goals.unlock')} onPress={() => router.push('/paywall')} />
        </View>
      ) : null}
      <ErrorView error={saveError} style={{ marginTop: 12 }} />
      <Button title={t('goals.save')} onPress={save} loading={busy} disabled={!data} style={{ marginTop: 20 }} />
    </Screen>
  );
}
