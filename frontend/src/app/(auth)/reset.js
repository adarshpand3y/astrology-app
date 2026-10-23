import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, View } from 'react-native';

import { authApi } from '../../api/endpoints';
import { AuthScreen } from '../../components/AuthScreen';
import { Button, ErrorView, Field, PasswordField } from '../../components/ui';
import { useI18n } from '../../i18n';
import { fieldErrors } from '../../utils/format';

export default function Reset() {
  const { t } = useI18n();
  const router = useRouter();
  const { email } = useLocalSearchParams();
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const errs = fieldErrors(error);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await authApi.confirmReset(email, code, password);
      Alert.alert(t('auth.resetTitle'), t('auth.resetDone'));
      router.dismissTo('/sign-in');
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthScreen title={t('auth.setPassword')} sub={t('auth.verifyHint', { email })}>
      {!errs.new_password ? <ErrorView error={error} /> : null}
      <View style={{ gap: 14 }}>
        <Field label={t('auth.code')} value={code} onChangeText={(v) => setCode(v.replace(/\D/g, '').slice(0, 6))}
          keyboardType="number-pad" autoComplete="one-time-code" textContentType="oneTimeCode" maxLength={6} />
        <PasswordField label={t('auth.newPassword')} value={password} onChangeText={setPassword}
          placeholder={t('auth.newPasswordPh')} autoComplete="new-password" textContentType="newPassword" error={errs.new_password} />
      </View>
      <Button title={t('common.save')} onPress={submit} loading={busy} disabled={code.length !== 6 || password.length < 8} style={{ marginTop: 22 }} />
    </AuthScreen>
  );
}
