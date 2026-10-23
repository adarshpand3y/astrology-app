import { useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { View } from 'react-native';

import { authApi } from '../../api/endpoints';
import { AuthScreen } from '../../components/AuthScreen';
import { BackLink, Button, ErrorView, Field, T, TextLink } from '../../components/ui';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { KIND } from '../../theme';

export default function Verify() {
  const { t } = useI18n();
  const params = useLocalSearchParams();
  const { verifyEmail } = useAuth();
  const email = params.email || '';
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);

  useEffect(() => {
    if (params.resend && params.email) {
      authApi.resendVerification(params.email).then(() => setNotice(t('auth.codeSent'))).catch(setError);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resend = async () => {
    setError(null);
    try {
      await authApi.resendVerification(email);
      setNotice(t('auth.codeSent'));
    } catch (e) { setError(e); }
  };

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await verifyEmail(email, code);
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <AuthScreen title={t('auth.verifyTitle')} sub={t('auth.verifyHint', { email })}>
      <View style={{ position: 'absolute', top: -6, left: -4 }}><BackLink label={t('common.back')} /></View>
      <ErrorView error={error} />
      {notice ? <T v="small" style={{ color: KIND.good.solid, marginBottom: 10 }}>{notice}</T> : null}
      <Field label={t('auth.code')} value={code} onChangeText={(v) => setCode(v.replace(/\D/g, '').slice(0, 6))}
        keyboardType="number-pad" autoComplete="one-time-code" textContentType="oneTimeCode" maxLength={6}
        inputStyle={{ fontSize: 22, letterSpacing: 8, textAlign: 'center' }} />
      <Button title={t('auth.verify')} onPress={submit} loading={busy} disabled={code.length !== 6} style={{ marginTop: 22 }} />
      <View style={{ alignItems: 'center', marginTop: 18 }}>
        <TextLink title={t('auth.resend')} onPress={resend} style={{ fontSize: 13 }} />
      </View>
    </AuthScreen>
  );
}
