import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import { authApi } from '../../api/endpoints';
import { AuthScreen, EMAIL_RE } from '../../components/AuthScreen';
import { Button, ErrorView, Field, PasswordField, Rich, Row, SoftPanel, T } from '../../components/ui';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { useTheme } from '../../theme';
import { fieldErrors } from '../../utils/format';

/** Step 0 of sign-up: just email + password. Birth details and goals follow in onboarding. */
export default function SignUp() {
  const { t } = useI18n();
  const th = useTheme();
  const router = useRouter();
  const { acceptTokens } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const server = fieldErrors(error);

  const errs = tried ? {
    email: !EMAIL_RE.test(email.trim()) ? t('auth.invalidEmail') : server.email,
    password: password.length < 8 ? t('auth.shortPassword') : server.password,
  } : {};

  const submit = async () => {
    setTried(true);
    if (!EMAIL_RE.test(email.trim()) || password.length < 8) return;
    setBusy(true);
    setError(null);
    try {
      const normalized = email.trim().toLowerCase();
      const r = await authApi.register({ email: normalized, password });
      if (r.access) await acceptTokens(r); // verification disabled on the server
      else router.replace({ pathname: '/verify', params: { email: normalized } });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  // Only hide the general error when a field below actually shows it.
  const hasFieldError = Boolean(server.email || server.password);

  return (
    <AuthScreen title={t('auth.createTitle')} sub={t('auth.createSub')}>
      {!hasFieldError ? <ErrorView error={error} /> : null}
      <View style={{ gap: 14, marginTop: 6 }}>
        <Field label={t('auth.email')} value={email} onChangeText={setEmail} placeholder={t('auth.emailPh')}
          autoCapitalize="none" keyboardType="email-address" autoComplete="email" error={errs.email} />
        <PasswordField label={t('auth.password')} value={password} onChangeText={setPassword}
          placeholder={t('auth.newPasswordPh')} autoComplete="new-password" textContentType="newPassword"
          error={errs.password} onSubmitEditing={submit} />
      </View>

      <SoftPanel n={0.15} style={{ marginTop: 24, flexDirection: 'row', gap: 10 }}>
        <Text style={{ color: th.c.accent, fontSize: 14, marginTop: 1 }}>◈</Text>
        <Rich v="caption" text={t('auth.trust')} style={{ flex: 1, lineHeight: 17 }} />
      </SoftPanel>
      <Button title={t('auth.createCta')} onPress={submit} loading={busy} style={{ marginTop: 12, paddingVertical: 16 }} />
      <Row gap={0} style={{ justifyContent: 'center', marginTop: 16 }}>
        <T v="small" style={{ fontSize: 13 }}>{t('auth.haveAccount')}</T>
        <Text onPress={() => router.back()} style={[th.font.ui(600), { fontSize: 13, color: th.c.accent }]}>{t('auth.signInLink')}</Text>
      </Row>
    </AuthScreen>
  );
}
