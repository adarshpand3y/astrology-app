// Expo app config generated from brand.config.js + environment variables.
const brand = require('./brand.config');

const lightBg = brand.theme.bases[brand.theme.base][0];
const APP_ENV = process.env.APP_ENV || process.env.EXPO_PUBLIC_APP_ENV || 'development';
// Android release builds block plain http://. Allow it only when the build points at an http
// backend (e.g. a LAN dev server); https builds stay locked down.
const HTTP_API = /^http:\/\//i.test(process.env.EXPO_PUBLIC_API_URL || '');

module.exports = () => ({
  expo: {
    name: brand.name,
    slug: brand.slug,
    scheme: brand.scheme,
    version: brand.version,
    owner: brand.owner,
    orientation: 'portrait',
    icon: brand.assets.icon,
    userInterfaceStyle: 'automatic',
    ios: {
      supportsTablet: true,
      bundleIdentifier: brand.iosBundleIdentifier,
    },
    android: {
      package: brand.androidPackage,
      // Must increase with every build installed over an older one; some phones (OnePlus, Oppo,
      // Realme…) only refresh the cached app icon when it does. scripts/build-lan-apk.ps1 sets it.
      versionCode: Number(process.env.ANDROID_VERSION_CODE) || 1,
      // On-time alerts: user-granted on Android 14+ ("Alarms & reminders"), granted at install on
      // 12-13. Declared by modules/exact-alarms too; listed here so it's visible. The app asks for
      // it once and the Alerts screen offers it while it's off.
      permissions: ['android.permission.SCHEDULE_EXACT_ALARM'],
      adaptiveIcon: {
        backgroundColor: brand.assets.adaptiveBackgroundColor || lightBg,
        foregroundImage: brand.assets.adaptiveForeground,
        backgroundImage: brand.assets.adaptiveBackground,
        monochromeImage: brand.assets.adaptiveMonochrome,
      },
    },
    web: { favicon: brand.assets.favicon },
    plugins: [
      'expo-router',
      'expo-status-bar',
      'expo-secure-store',
      'expo-localization',
      'expo-font',
      ['expo-notifications', { icon: brand.assets.notificationIcon, color: brand.theme.accents[brand.theme.accent][0] }],
      ['expo-build-properties', { android: { usesCleartextTraffic: HTTP_API } }],
      [
        'expo-splash-screen',
        {
          image: brand.assets.splashImage,
          imageWidth: 180,
          resizeMode: 'contain',
          backgroundColor: lightBg,
          dark: {
            image: brand.assets.splashImage,
            backgroundColor: '#100F17',
          },
        },
      ],
    ],
    extra: {
      appEnv: APP_ENV,
      brand,
    },
  },
});
