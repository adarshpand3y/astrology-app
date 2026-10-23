import { useRouter } from 'expo-router';
import { useState } from 'react';

import { remediesApi } from '../../api/endpoints';
import { GoalPicker } from '../../components/GoalPicker';
import { OnboardingScreen } from '../../components/Onboarding';
import { Button, ErrorView, Loading, T } from '../../components/ui';
import { useGoals } from '../../hooks/data';
import { setCached } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { useTheme } from '../../theme';
import { todayISO } from '../../utils/format';

/** Onboarding step 2: pick 1-3 goals; the server suggests remedies for them. */
export default function OnboardingGoals() {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const { data, error, loading, refetch } = useGoals();
  const [picked, setPicked] = useState(null);
  const [hint, setHint] = useState(null);
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const max = data?.max || 1;
  const goals = picked ?? (data?.goals || []).slice(0, max);

  const submit = async () => {
    if (!goals.length) { setHint(t('onboarding.goalsPick')); return; }
    if (goals.length > max) { setHint(t('onboarding.goalsMax', { n: max })); return; }
    setBusy(true);
    setSaveError(null);
    try {
      const r = await remediesApi.setGoals(goals, todayISO());
      setCached('onboarding:remedies', r);
      router.push('/onboarding/remedies');
    } catch (e) {
      setSaveError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <OnboardingScreen step={2} title={t('onboarding.goalsTitle')}
      sub={max === 1 ? t('onboarding.goalsSubOne') : t('onboarding.goalsSub', { n: max })}>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <GoalPicker catalogue={data.catalogue} value={goals} max={max}
          onChange={(v) => { setPicked(v); setHint(null); }}
          onLimit={() => setHint(t('onboarding.goalsMax', { n: max }))} />
      ) : null}
      {hint ? <T v="caption" style={{ color: th.kind.bad.solid, marginTop: 12, textAlign: 'center' }}>{hint}</T> : null}
      {data && !data.is_pro ? (
        <T v="caption" style={{ marginTop: 14, textAlign: 'center' }}>{t('goals.freeNote', { n: data.pro_max })}</T>
      ) : null}
      <ErrorView error={saveError} style={{ marginTop: 12 }} />
      <Button title={t('onboarding.goalsCta')} onPress={submit} loading={busy} disabled={!data}
        style={{ marginTop: 20, paddingVertical: 16 }} />
    </OnboardingScreen>
  );
}
