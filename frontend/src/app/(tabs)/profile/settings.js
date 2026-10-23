import Constants from 'expo-constants';
import { useState } from 'react';
import { Alert, View } from 'react-native';

import { authApi } from '../../../api/endpoints';
import { LocationPicker } from '../../../components/LocationPicker';
import { BackLink, Button, Card, ErrorView, PasswordField, Row, Screen, Seg, T } from '../../../components/ui';
import { API_URL, APP_ENV, brand } from '../../../config/env';
import { LANGUAGE_NAMES, LANGUAGES, useI18n } from '../../../i18n';
import { useAuth } from '../../../state/AuthContext';
import { usePrefs } from '../../../state/PrefsContext';
import { fieldErrors } from '../../../utils/format';

function Section({ title, children }) {
  return (
    <>
      <T v="eyebrow" style={{ marginTop: 22, marginBottom: 10, marginHorizontal: 2 }}>{title}</T>
      <Card radius={18} pad={16}>{children}</Card>
    </>
  );
}

export default function Settings() {
  const { t } = useI18n();
  const { prefs, update } = usePrefs();
  const { user, updateMe, signOut, acceptTokens, signOutLocal } = useAuth();

  return (
    <Screen>
      <BackLink label={t('tabs.profile')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2 }}>{t('settings.title')}</T>

      <Section title={t('settings.appearance')}>
        <T v="label" style={{ marginBottom: 8 }}>{t('settings.theme')}</T>
        <Seg value={prefs.themeMode} onChange={(v) => update({ themeMode: v })}
          options={['system', 'light', 'dark'].map((v) => ({ value: v, label: t(`settings.${v}`) }))} />
        {LANGUAGES.length > 1 ? (
          <>
            <T v="label" style={{ marginTop: 16, marginBottom: 8 }}>{t('settings.language')}</T>
            <Seg value={prefs.language} onChange={(v) => update({ language: v })}
              options={[{ value: 'system', label: t('settings.system') }, ...LANGUAGES.map((l) => ({ value: l, label: LANGUAGE_NAMES[l] }))]} />
          </>
        ) : null}
        {brand.features.southIndianChart ? (
          <>
            <T v="label" style={{ marginTop: 16, marginBottom: 8 }}>{t('settings.chartStyle')}</T>
            <Seg value={prefs.chartStyle} onChange={(v) => update({ chartStyle: v })}
              options={[{ value: 'north', label: t('settings.north') }, { value: 'south', label: t('settings.south') }]} />
          </>
        ) : null}
      </Section>

      <Section title={t('settings.location')}>
        <LocationPicker icon="target" value={user?.current_place}
          onChange={(p) => updateMe({ current_place_id: p.id }).catch((e) => Alert.alert(t('common.unknownError'), e.message))} />
      </Section>

      <Section title={t('settings.account')}>
        <T weight={600}>{user?.full_name}</T>
        <T v="small" style={{ marginBottom: 14 }}>{user?.email}</T>
        <ChangePassword onDone={acceptTokens} />
        <Button variant="outline" title={t('settings.logout')} onPress={signOut} style={{ marginTop: 10 }} />
        {brand.features.accountDeletion ? <DeleteAccount onDeleted={signOutLocal} /> : null}
      </Section>

      <Section title={t('settings.about')}>
        <Row style={{ justifyContent: 'space-between' }}>
          <T v="small">{brand.name}</T>
          <T v="small">{t('settings.version')} {Constants.expoConfig?.version || brand.version}</T>
        </Row>
        <Row style={{ justifyContent: 'space-between', marginTop: 8 }}>
          <T v="small">{t('settings.server')}</T>
          <T v="tiny" style={{ flexShrink: 1, textAlign: 'right' }}>{API_URL} ({APP_ENV})</T>
        </Row>
      </Section>
    </Screen>
  );
}

function ChangePassword({ onDone }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const errs = fieldErrors(error);

  if (!open) return <Button variant="outline" title={t('settings.changePassword')} onPress={() => setOpen(true)} />;
  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await onDone(await authApi.changePassword(oldPw, newPw));
      setOpen(false);
      setOldPw('');
      setNewPw('');
      Alert.alert(t('settings.changePassword'), t('settings.passwordChanged'));
    } catch (e) { setError(e); } finally { setBusy(false); }
  };
  return (
    <View style={{ gap: 12 }}>
      {!Object.keys(errs).length ? <ErrorView error={error} /> : null}
      <PasswordField label={t('settings.currentPassword')} value={oldPw} onChangeText={setOldPw} error={errs.old_password} />
      <PasswordField label={t('settings.newPassword')} value={newPw} onChangeText={setNewPw} error={errs.new_password} />
      <Button title={t('common.save')} onPress={submit} loading={busy} disabled={!oldPw || newPw.length < 8} />
      <Button variant="outline" title={t('common.cancel')} onPress={() => setOpen(false)} />
    </View>
  );
}

function DeleteAccount({ onDeleted }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [pw, setPw] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  if (!open) return <Button variant="outline" title={t('settings.deleteAccount')} onPress={() => setOpen(true)} style={{ marginTop: 10 }} />;
  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await authApi.deleteMe(pw);
      await onDeleted();
    } catch (e) { setError(e); setBusy(false); }
  };
  return (
    <View style={{ gap: 12, marginTop: 14 }}>
      <T v="small">{t('settings.deleteWarning')}</T>
      <ErrorView error={error} />
      <PasswordField label={t('auth.password')} value={pw} onChangeText={setPw} />
      <Button variant="danger" title={t('settings.deleteAccount')} onPress={submit} loading={busy} disabled={!pw} />
      <Button variant="outline" title={t('common.cancel')} onPress={() => setOpen(false)} />
    </View>
  );
}
