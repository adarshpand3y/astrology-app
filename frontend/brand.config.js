/**
 * Single source of truth for white-labelling the app.
 *
 * Change identity, palette, features and defaults here; no screen code needs to
 * change. Identity fields (name, ids, icons) take effect on the next `expo start`
 * (and need a new native build for store apps).
 */
module.exports = {
  // --- Identity -------------------------------------------------------------------
  name: 'Guru Drishti',
  shortName: 'Guru Drishti',
  tagline: 'Vedic daily companion',
  taglineHi: 'वैदिक दैनिक साथी',
  slug: 'guru-drishti',
  scheme: 'gurudrishti',
  version: '1.0.0',
  iosBundleIdentifier: 'com.gurudrishti.app',
  androidPackage: 'com.gurudrishti.app',
  owner: undefined, // EAS account owner, if any

  // --- Assets ---------------------------------------------------------------------
  // Sources (plus SVGs and web sizes) live in docs/icons.
  assets: {
    icon: './assets/icon.png',
    splashImage: './assets/splash-icon.png', // transparent, used on both light and dark splash
    adaptiveForeground: './assets/adaptive-icon-foreground.png',
    adaptiveBackground: './assets/adaptive-icon-background.png',
    adaptiveBackgroundColor: '#100F17', // shown behind the background image while it loads
    adaptiveMonochrome: './assets/adaptive-icon-monochrome.png',
    notificationIcon: './assets/notification-icon.png', // Android status bar: white on transparent
    favicon: './assets/favicon.png',
  },
  logoGlyph: '☽', // the breathing orb on sign-in / sign-up

  // --- API ------------------------------------------------------------------------
  // Used when EXPO_PUBLIC_API_URL is not set and the app is not running in dev.
  apiUrl: 'https://api.example.com',
  devApiPort: 8000,

  // --- Theme ----------------------------------------------------------------------
  // Pick one accent and one light background; every tint is derived from them.
  theme: {
    accent: 'dawn',
    base: 'paper',
    accents: {
      // [light accent, light accent-dark, dark-mode accent, dark-mode accent-dark]
      dawn: ['#B0722F', '#8A5A22', '#DCA85F', '#EBC48C'],
      twilight: ['#4C5BA6', '#3B4890', '#8E9BE0', '#B2BBED'],
      grove: ['#5E8A6B', '#496F56', '#86B394', '#A9CDB5'],
      terracotta: ['#B0654A', '#8C4E38', '#D89377', '#E8AF97'],
      amethyst: ['#8A5A8F', '#6D4372', '#BE93C2', '#D6B2D9'],
      ink: ['#566579', '#404C5D', '#93A2B8', '#B4C0D0'],
    },
    bases: {
      // light mode only: [canvas, surface, raised]
      paper: ['#F1ECE2', '#FFFFFF', '#F4EFE6'],
      sand: ['#ECE3D3', '#FBF7EF', '#F2EADB'],
      mist: ['#EBEDF1', '#FFFFFF', '#F2F3F6'],
      fog: ['#EAE7E1', '#FBFAF7', '#F1EEE8'],
      blush: ['#F1E8E3', '#FFFDFB', '#F6EEE9'],
    },
  },

  // --- Feature flags --------------------------------------------------------------
  features: {
    decisionAssistant: true,
    panchang: true,
    remedies: true,
    journal: true,
    alerts: true,
    paywall: true,          // when false, Pro gates simply show the "Pro" lock without an upsell
    southIndianChart: true,
    moreDivisions: true,    // D2–D60 beyond Rashi/Navamsa
    birthDetails: true,     // planets table, birth panchang, avakhada
    hindi: true,            // language switcher
    accountDeletion: true,
  },

  // --- Defaults (users can change these in Settings) ---------------------------------
  defaults: {
    language: 'system', // 'system' | 'en' | 'hi'
    themeMode: 'system', // 'system' | 'light' | 'dark'
    chartStyle: 'north', // 'north' | 'south'
    nodeMode: 'mean', // 'mean' | 'true'
    ayanamsa: 'lahiri',
  },

  support: {
    email: 'support@example.com',
    privacyUrl: 'https://example.com/privacy',
    termsUrl: 'https://example.com/terms',
  },
};
