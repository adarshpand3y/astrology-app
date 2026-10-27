import { Linking, Platform } from 'react-native';

import { APP_VERSION } from '../api/client';
import { brand } from '../config/env';
import { useI18n } from '../i18n';
import { AuthScreen } from './AuthScreen';
import { Button, T } from './ui';

/** The store page for this app: [app-scheme URL, web fallback]. */
function storeUrls() {
  if (Platform.OS === 'ios') {
    if (!brand.iosAppStoreId) return [null, `https://apps.apple.com/search?term=${encodeURIComponent(brand.name)}`];
    return [`itms-apps://apps.apple.com/app/id${brand.iosAppStoreId}`, `https://apps.apple.com/app/id${brand.iosAppStoreId}`];
  }
  return [`market://details?id=${brand.androidPackage}`, `https://play.google.com/store/apps/details?id=${brand.androidPackage}`];
}

async function openStore() {
  const [app, web] = storeUrls();
  try {
    if (app) { await Linking.openURL(app); return; }
  } catch { /* no store app on this phone; fall through to the website */ }
  await Linking.openURL(web).catch(() => {});
}

/** Shown in place of the whole app once the server rejects this build as too old. */
export function UpdateRequired({ minVersion }) {
  const { t } = useI18n();
  const store = Platform.OS === 'ios' ? t('update.appStore') : t('update.playStore');
  return (
    <AuthScreen title={t('update.title')} sub={t('update.sub')}>
      <Button title={t('update.cta', { store })} onPress={openStore} style={{ marginTop: 8, paddingVertical: 16 }} />
      <T v="caption" style={{ marginTop: 14, textAlign: 'center' }}>
        {minVersion ? t('update.versions', { v: APP_VERSION, min: minVersion }) : t('update.version', { v: APP_VERSION })}
      </T>
    </AuthScreen>
  );
}
