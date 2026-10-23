import { useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { AuthScreen, EMAIL_RE } from '../../components/AuthScreen';
import { Button, ErrorView, Field, PasswordField, Row, T, TextLink } from '../../components/ui';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { useTheme } from '../../theme';

export default function SignIn() {
  const { t } = useI18n();
  const th = useTheme();
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const emailErr = tried && !EMAIL_RE.test(email.trim());
  const pwErr = tried && password.length < 8;

  const submit = async () => {
    setTried(true);
    if (!EMAIL_RE.test(email.trim()) || password.length < 8) return;
    setBusy(true);
    setError(null);
    try {
      await signIn(email, password);
    } catch (e) {
      if (e.code === 'email_not_verified') {
        router.push({ pathname: '/verify', params: { email: email.trim().toLowerCase(), resend: '1' } });
      } else {
        setError(e);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthScreen title={t('auth.welcomeBack')} sub={t('auth.signInSub')}>
      <ErrorView error={error} />
      <View style={{ gap: 14 }}>
        <Field label={t('auth.email')} value={email} onChangeText={setEmail} placeholder={t('auth.emailPh')}
          autoCapitalize="none" keyboardType="email-address" autoComplete="email" textContentType="emailAddress"
          error={emailErr ? t('auth.invalidEmail') : null} />
        <PasswordField label={t('auth.password')} value={password} onChangeText={setPassword} placeholder={t('auth.passwordPh')}
          autoComplete="password" textContentType="password" onSubmitEditing={submit} returnKeyType="go"
          labelRight={<TextLink title={t('auth.forgot')} style={{ fontSize: 11.5 }}
            onPress={() => router.push({ pathname: '/forgot', params: { email } })} />}
          error={pwErr ? t('auth.shortPassword') : null} />
      </View>
      <Button title={t('auth.signIn')} onPress={submit} loading={busy} style={{ marginTop: 22 }} />

      <Row gap={12} style={{ marginTop: 22, marginBottom: 4 }}>
        <View style={{ flex: 1, height: 1, backgroundColor: th.c.hair }} />
        <T v="tiny">{t('auth.orNew')}</T>
        <View style={{ flex: 1, height: 1, backgroundColor: th.c.hair }} />
      </Row>
      <Button variant="outline" title={t('auth.createAccount')} onPress={() => router.push('/sign-up')} style={{ marginTop: 10, paddingVertical: 14 }} />

      <View style={{ flex: 1, minHeight: 24 }} />
      <T v="tiny" style={{ textAlign: 'center', lineHeight: 16.5, marginTop: 24 }}>
        {t('auth.terms')}{'\n'}{t('auth.private')}
      </T>
    </AuthScreen>
  );
}
