import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { remediesApi } from '../api/endpoints';
import { GoalPicker } from '../components/GoalPicker';
import { ProIcon } from '../components/Icons';
import { Button, ErrorView, Loading, Row, Screen, SoftPanel, T, TextLink } from '../components/ui';
import { useGoals } from '../hooks/data';
import { invalidate } from '../hooks/useApi';
import { useI18n } from '../i18n';
import { useAuth } from '../state/AuthContext';
import { useTheme } from '../theme';
import { todayISO } from '../utils/format';

/**
 * Modal: a chart's goals (the active chart, or `?profile=<id>`). Remedies for new goals are added;
 * untouched ones for dropped goals go. Right after adding a chart (`isNew`), goals can be skipped:
 * the chart then follows its Mahadasha and Antardasha lords' remedies. On the free plan only your
 * own chart takes a goal.
 */
export default function Goals() {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const { profile, isNew } = useLocalSearchParams();
  const { refreshUser } = useAuth();
  const { data, error, loading, refetch } = useGoals(profile);
  const [picked, setPicked] = useState(null);
  const [hint, setHint] = useState(null);
  const [busy, setBusy] = useState(null); // 'save' | 'skip'
  const [saveError, setSaveError] = useState(null);
  const max = data?.max ?? 1;
  const locked = data && max === 0; // someone else's chart on the free plan
  const canSkip = !!isNew || (data && !data.chosen);
  // A free user who picked several goals while on Pro keeps them until they save again.
  const goals = picked ?? data?.goals ?? [];
  const self = data?.profile.relation === 'self';

  const store = async (list, kind) => {
    setBusy(kind);
    setSaveError(null);
    try {
      await remediesApi.setGoals(list, todayISO(), profile);
      ['goals:', 'remedies:', 'remedy-history:', 'schedule:', 'profiles'].forEach((k) => invalidate(k));
      await refreshUser();
      router.back();
    } catch (e) {
      setBusy(null);
      if (e.code === 'pro_required') router.push('/paywall');
      else setSaveError(e);
    }
  };
  const save = () => {
    if (!goals.length) { setHint(t('onboarding.goalsPick')); return; }
    if (goals.length > max) { setHint(t('onboarding.goalsMax', { n: max })); return; }
    store(goals, 'save');
  };

  return (
    <Screen tabs={false}>
      <Row style={{ justifyContent: 'space-between', paddingTop: 6, paddingBottom: 6 }}>
        <T v="screenTitle" style={{ flex: 1 }} numberOfLines={1}>
          {!data || self ? t('goals.title') : t('goals.titleFor', { name: data.profile.name.split(' ')[0] })}
        </T>
        <Pressable onPress={() => router.back()} hitSlop={10} style={{ width: 30, height: 30, borderRadius: 15, backgroundColor: th.c.muted, alignItems: 'center', justifyContent: 'center' }}>
          <Text style={{ color: th.c.ink2 }}>✕</Text>
        </Pressable>
      </Row>
      <T v="small" style={{ marginBottom: 16 }}>
        {isNew ? t('goals.subNew', { name: data?.profile.name || '' }) : t('goals.sub')}
      </T>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />

      {locked ? (
        <SoftPanel style={{ padding: 16, borderRadius: 16 }}>
          <Row gap={7} style={{ marginBottom: 6 }}>
            <ProIcon size={14} />
            <T weight={700} style={{ fontSize: 13, color: th.c.accentDark }}>{t('common.pro')}</T>
          </Row>
          <T v="small" style={{ marginBottom: 12 }}>{t('goals.lockedOther', { name: data.profile.name.split(' ')[0] })}</T>
          <Button small title={t('common.unlock')} onPress={() => router.push('/paywall')} />
        </SoftPanel>
      ) : data ? (
        <>
          {max > 1 ? <T v="caption" style={{ marginBottom: 10 }}>{t('goals.count', { n: goals.length, max })}</T> : null}
          <GoalPicker catalogue={data.catalogue} value={goals} max={max}
            onChange={(v) => { setPicked(v); setHint(null); }}
            onLimit={() => setHint(t('onboarding.goalsMax', { n: max }))} />
        </>
      ) : null}
      {hint ? <T v="caption" style={{ color: th.kind.bad.solid, marginTop: 12, textAlign: 'center' }}>{hint}</T> : null}
      {data && !data.is_pro && !locked ? (
        <View style={{ alignItems: 'center', marginTop: 14, gap: 6 }}>
          <T v="caption" style={{ textAlign: 'center' }}>{t('goals.freeNote', { n: data.pro_max })}</T>
          <TextLink title={t('goals.unlock')} onPress={() => router.push('/paywall')} />
        </View>
      ) : null}
      <ErrorView error={saveError} style={{ marginTop: 12 }} />
      {!locked ? (
        <Button title={t('goals.save')} onPress={save} loading={busy === 'save'} disabled={!data || !!busy}
          style={{ marginTop: 20 }} />
      ) : null}
      {canSkip && data ? (
        <View style={{ marginTop: 12 }}>
          <Button title={t('goals.skip')} variant="secondary" onPress={() => store([], 'skip')}
            loading={busy === 'skip'} disabled={!!busy} />
          <T v="caption" style={{ textAlign: 'center', marginTop: 8 }}>{t('goals.skipNote')}</T>
        </View>
      ) : null}
    </Screen>
  );
}
