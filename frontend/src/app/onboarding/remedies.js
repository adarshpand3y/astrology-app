import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';

import { remediesApi } from '../../api/endpoints';
import { OnboardingScreen } from '../../components/Onboarding';
import { RemedyCard } from '../../components/RemedyCard';
import { Button, ErrorView, Loading, Row, T } from '../../components/ui';
import { invalidate, useApi } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { useTheme } from '../../theme';
import { confirm } from '../../utils/confirm';
import { todayISO } from '../../utils/format';

const ONBOARDING_REMEDIES = 'onboarding:remedies'; // primed by the goals step

/** Onboarding step 3: review the suggested remedies, edit or remove any, then on to preferences. */
export default function OnboardingRemedies() {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const { data, error, loading, refetch } = useApi(ONBOARDING_REMEDIES, () => remediesApi.list(todayISO()));
  const [err, setErr] = useState(null);

  const remove = async (r) => {
    if (!(await confirm(t('remedies.remove'), t('remedies.removeConfirm', { title: r.title }),
      { ok: t('remedies.remove'), cancel: t('common.cancel'), destructive: true }))) return;
    try {
      await remediesApi.remove(r.id);
      refetch();
    } catch (e) {
      setErr(e);
    }
  };

  const next = () => {
    invalidate('remedies:');
    router.push('/onboarding/preferences');
  };

  const groups = data ? [
    ...data.goals.map((g) => ({ key: g.key, title: g.label, glyph: g.glyph, items: data.remedies.filter((r) => r.goal === g.key) })),
    // Remedies for the lagna lord, Chandra and the current dasha lords, whatever the goals.
    { key: '', title: t('remedies.fromChart'), glyph: '✦', items: data.remedies.filter((r) => !data.goals.some((g) => g.key === r.goal)) },
  ].filter((g) => g.items.length) : [];

  const action = (label, onPress) => (
    <Pressable onPress={onPress} hitSlop={6} style={{ paddingVertical: 6, paddingHorizontal: 4 }}>
      <T v="tiny" weight={600} style={{ color: th.c.accent, fontSize: 12 }}>{label}</T>
    </Pressable>
  );

  return (
    <OnboardingScreen step={3} title={t('onboarding.remediesTitle')} sub={t(data?.locked ? 'onboarding.remediesSubFree' : 'onboarding.remediesSub')}>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {groups.map((g) => (
        <View key={g.key || 'other'} style={{ marginBottom: 18 }}>
          {g.title ? <T v="eyebrow" style={{ marginBottom: 9, marginHorizontal: 2 }}>{g.glyph}  {g.title}</T> : null}
          <View style={{ gap: 9 }}>
            {g.items.map((r) => (
              <RemedyCard key={r.id} remedy={r} right={(
                <View style={{ alignItems: 'flex-end' }}>
                  {/* Editing is Pro; the paywall isn't reachable mid-onboarding, so free users only remove. */}
                  {!data.locked ? action(t('remedies.edit'), () => router.push(`/onboarding/edit/${r.id}`)) : null}
                  {action(t('remedies.remove'), () => remove(r))}
                </View>
              )} />
            ))}
          </View>
        </View>
      ))}
      <ErrorView error={err} style={{ marginTop: 4 }} />
      <Button title={t('onboarding.remediesCta')} onPress={next} disabled={!data}
        style={{ marginTop: 10, paddingVertical: 16 }} />
      <Row style={{ justifyContent: 'center', marginTop: 14 }}>
        <Pressable onPress={() => router.back()} hitSlop={8}>
          <T v="small" style={{ fontSize: 13 }}>‹ {t('onboarding.goalsTitle')}</T>
        </Pressable>
      </Row>
    </OnboardingScreen>
  );
}
