import { BackHandler, Linking, Modal, Platform, View } from 'react-native';

import { APP_VERSION } from '../api/client';
import { brand } from '../config/env';
import { useI18n } from '../i18n';
import { useTheme } from '../theme';
import { Icon } from './Icons';
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

// iOS apps may not close themselves (App Review rejects it), so Exit is Android-only there.
const CAN_EXIT = Platform.OS === 'android';

/**
 * Blocking dialog over the (dimmed) app once the server rejects this build as too old: update from
 * the store, or exit (Android). Back and taps outside do nothing.
 */
export function UpdateRequired() {
  const th = useTheme();
  const { t } = useI18n();
  const store = Platform.OS === 'ios' ? t('update.appStore') : t('update.playStore');
  return (
    <Modal visible transparent animationType="fade" statusBarTranslucent onRequestClose={() => {}}>
      <View style={{ flex: 1, backgroundColor: th.c.scrim, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <View
          accessibilityViewIsModal
          style={[{
            width: '100%', maxWidth: 380, backgroundColor: th.c.surface, borderRadius: 24,
            paddingTop: 26, paddingBottom: 20, paddingHorizontal: 22, alignItems: 'center',
          }, th.shadow('card')]}
        >
          <View style={{ width: 56, height: 56, borderRadius: 18, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
            <Icon name="cellphone-arrow-down" size={28} color={th.c.accent} />
          </View>
          <T v="screenTitle" style={{ marginTop: 16, fontSize: 21, textAlign: 'center' }} accessibilityRole="header">{t('update.title')}</T>
          <T v="small" style={{ marginTop: 8, textAlign: 'center', fontSize: 13.5, lineHeight: 20 }}>{t('update.sub')}</T>
          <T v="caption" style={{ marginTop: 10, textAlign: 'center' }}>{t('update.version', { v: APP_VERSION })}</T>
          <Button title={t('update.cta', { store })} onPress={openStore} style={{ marginTop: 20, alignSelf: 'stretch' }} />
          {CAN_EXIT ? (
            <Button title={t('update.exit')} variant="secondary" onPress={() => BackHandler.exitApp()}
              style={{ marginTop: 10, alignSelf: 'stretch' }} />
          ) : null}
        </View>
      </View>
    </Modal>
  );
}
