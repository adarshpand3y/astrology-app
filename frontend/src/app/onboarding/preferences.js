import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable } from 'react-native';

import { alertsApi } from '../../api/endpoints';
import { OnboardingScreen } from '../../components/Onboarding';
import { ALERT_FIELDS, AlertToggles, AppearanceSettings } from '../../components/Preferences';
import { Button, Card, ErrorView, Loading, Row, T } from '../../components/ui';
import { useAlertPrefs } from '../../hooks/data';
import { invalidate, setCached } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { requestPermission } from '../../notifications';
import { useAuth } from '../../state/AuthContext';

/** Onboarding step 4: appearance and which alerts to receive, then enter the app. */
export default function OnboardingPreferences() {
  const { t } = useI18n();
  const router = useRouter();
  const { refreshUser } = useAuth();
  const prefs = useAlertPrefs();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const p = prefs.data;
  // The paywall isn't reachable mid-onboarding, so free users only see the free alerts.
  const fields = p ? ALERT_FIELDS.filter((f) => p.is_pro || !p.pro_fields.includes(f)) : [];

  const toggle = async (field) => {
    const next = !p[field];
    setCached('alert-prefs', { ...p, [field]: next });
    try {
      setCached('alert-prefs', await alertsApi.update({ [field]: next }));
    } catch (e) {
      setCached('alert-prefs', p);
      setErr(e);
    }
  };

  const begin = async () => {
    setBusy(true);
    setErr(null);
    try {
      if (fields.some((f) => p[f])) await requestPermission();
      invalidate('schedule:');
      invalidate('remedies:');
      await refreshUser(); // needs_onboarding flips to false and the app opens (the tabs sync alerts)
    } catch (e) {
      setErr(e);
      setBusy(false);
    }
  };

  return (
    <OnboardingScreen step={4} title={t('onboarding.prefsTitle')} sub={t('onboarding.prefsSub')}>
      <T v="eyebrow" style={{ marginBottom: 10, marginHorizontal: 2 }}>{t('settings.appearance')}</T>
      <Card radius={18} pad={16}>
        <AppearanceSettings />
      </Card>
      <T v="eyebrow" style={{ marginTop: 22, marginBottom: 10, marginHorizontal: 2 }}>{t('onboarding.prefsAlerts')}</T>
      {prefs.loading ? <Loading /> : null}
      <ErrorView error={prefs.error} onRetry={prefs.refetch} />
      {p ? <AlertToggles prefs={p} onToggle={toggle} fields={fields} /> : null}
      <T v="caption" style={{ marginTop: 10, marginHorizontal: 2 }}>{t('onboarding.prefsLater')}</T>
      <ErrorView error={err} style={{ marginTop: 12 }} />
      <Button title={t('onboarding.begin')} onPress={begin} loading={busy} disabled={!p}
        style={{ marginTop: 20, paddingVertical: 16 }} />
      <Row style={{ justifyContent: 'center', marginTop: 14 }}>
        <Pressable onPress={() => router.back()} hitSlop={8}>
          <T v="small" style={{ fontSize: 13 }}>‹ {t('onboarding.remediesTitle')}</T>
        </Pressable>
      </Row>
    </OnboardingScreen>
  );
}
