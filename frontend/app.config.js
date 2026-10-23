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
      // Lets alerts fire on the minute (period changes, Rahu Kaal). Granted at install up to
      // Android 13; on 14+ the user enables "Alarms & reminders" for the app, otherwise Android
      // delivers them a few minutes late.
      permissions: ['android.permission.SCHEDULE_EXACT_ALARM'],
      adaptiveIcon: {
        backgroundColor: lightBg,
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
      ['expo-notifications', { color: brand.theme.accents[brand.theme.accent][0] }],
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
