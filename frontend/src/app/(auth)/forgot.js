import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { authApi } from '../../api/endpoints';
import { AuthScreen, EMAIL_RE } from '../../components/AuthScreen';
import { BackLink, Button, ErrorView, Field } from '../../components/ui';
import { useI18n } from '../../i18n';

export default function Forgot() {
  const { t } = useI18n();
  const router = useRouter();
  const params = useLocalSearchParams();
  const [email, setEmail] = useState(params.email || '');
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setTried(true);
    if (!EMAIL_RE.test(email.trim())) return;
    setBusy(true);
    setError(null);
    try {
      const normalized = email.trim().toLowerCase();
      await authApi.requestReset(normalized);
      router.replace({ pathname: '/reset', params: { email: normalized } });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthScreen title={t('auth.resetTitle')} sub={t('auth.resetHint')}>
      <View style={{ position: 'absolute', top: -6, left: -4 }}><BackLink label={t('common.back')} /></View>
      <ErrorView error={error} />
      <Field label={t('auth.email')} value={email} onChangeText={setEmail} placeholder={t('auth.emailPh')} autoCapitalize="none"
        keyboardType="email-address" autoComplete="email"
        error={tried && !EMAIL_RE.test(email.trim()) ? t('auth.invalidEmail') : null} />
      <Button title={t('auth.sendCode')} onPress={submit} loading={busy} style={{ marginTop: 22 }} />
    </AuthScreen>
  );
}
