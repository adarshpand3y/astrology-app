import { useMemo } from 'react';
import { Platform, useColorScheme } from 'react-native';

import { brand } from '../config/env';
import { usePrefs } from '../state/PrefsContext';

const { accents, bases } = brand.theme;

// --- colour helpers -----------------------------------------------------------------
function hexToRgb(hex) {
  const h = hex.replace('#', '');
  const n = parseInt(h.length === 3 ? h.split('').map((c) => c + c).join('') : h, 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

/** `alpha('#B0722F', 0.15)` → rgba string (the design's "accent N% over transparent"). */
export function alpha(hex, a) {
  const [r, g, b] = hexToRgb(hex);
  return `rgba(${r},${g},${b},${a})`;
}

/** `mix('#B0722F', 0.45, '#ffffff')` → hex (CSS color-mix(in srgb, a 45%, b)). */
export function mix(a, pct, b) {
  const x = hexToRgb(a);
  const y = hexToRgb(b);
  const c = x.map((v, i) => Math.round(v * pct + y[i] * (1 - pct)));
  return `#${c.map((v) => v.toString(16).padStart(2, '0')).join('')}`;
}

// --- semantic timing colours (same in both themes) -------------------------------------
export const KIND = {
  good: { solid: '#5E8A6B', tint: 'rgba(94,138,107,.13)', text: '#4B7458' },
  neutral: { solid: '#B08A3A', tint: 'rgba(176,138,58,.14)', text: '#8C6D2B' },
  bad: { solid: '#B05A44', tint: 'rgba(176,90,68,.13)', text: '#9A4A36' },
};
export const ERROR = '#B05A44';

// --- fonts ------------------------------------------------------------------------------
export const FONTS = {
  display: { 400: 'Newsreader_400Regular', 500: 'Newsreader_500Medium', 600: 'Newsreader_600SemiBold' },
  ui: { 400: 'HankenGrotesk_400Regular', 500: 'HankenGrotesk_500Medium', 600: 'HankenGrotesk_600SemiBold', 700: 'HankenGrotesk_700Bold' },
  mono: { 400: 'SplineSansMono_400Regular', 500: 'SplineSansMono_500Medium', 600: 'SplineSansMono_600SemiBold' },
};

function palette(scheme, accentKey, baseKey) {
  const acc = accents[accentKey] || accents.dawn;
  const base = bases[baseKey] || bases.paper;
  if (scheme === 'dark') {
    return {
      bg: '#100F17', surface: '#1C1B27', surface2: '#25232F', sheet: '#1C1B27',
      ink: '#F0EDE6', ink2: '#A6A0AE', ink3: '#736D7C', inv: '#F0EDE6',
      hair: 'rgba(255,255,255,.10)', hair2: 'rgba(255,255,255,.18)', track: 'rgba(255,255,255,.10)',
      muted: 'rgba(255,255,255,.06)', tabBg: 'rgba(28,27,39,.94)', tabInactive: '#736D7C',
      accent: acc[2], accentDark: acc[3], onAccent: '#160F04', chartLine: 'rgba(200,190,220,.35)',
      shadow: '#000000', scrim: 'rgba(0,0,0,.5)', avatarBg: '#2E2A3D', avatarFg: acc[3],
    };
  }
  return {
    bg: base[0], surface: base[1], surface2: base[2], sheet: '#FBF9F4',
    ink: '#26221C', ink2: '#6E685D', ink3: '#A59E90', inv: '#26221C',
    hair: 'rgba(38,34,28,.08)', hair2: 'rgba(38,34,28,.15)', track: 'rgba(38,34,28,.08)',
    muted: 'rgba(38,34,28,.06)', tabBg: 'rgba(255,255,255,.94)', tabInactive: '#A9A294',
    accent: acc[0], accentDark: acc[1], onAccent: '#FFF8EE', chartLine: 'rgba(140,120,100,.4)',
    shadow: '#14101E', scrim: 'rgba(20,16,30,.34)', avatarBg: '#EDE4D3', avatarFg: '#8A6A2F',
  };
}

export function buildTheme(scheme, lang = 'en') {
  const c = palette(scheme, brand.theme.accent, brand.theme.base);
  // Latin display/UI fonts lack Devanagari: use the system font in Hindi.
  const latin = lang !== 'hi';
  const family = (kind, weight) => (latin ? FONTS[kind][weight] || FONTS[kind][500] : undefined);
  return {
    scheme,
    dark: scheme === 'dark',
    c,
    soft: (n) => alpha(c.accent, n),           // accentSoft tints
    gradient: [mix(c.accent, 0.45, '#ffffff'), c.accent],
    deep: mix(c.accent, 0.68, '#000000'),
    kind: KIND,
    font: {
      display: (w = 500) => ({ fontFamily: family('display', w), fontWeight: latin ? undefined : String(w) }),
      ui: (w = 400) => ({ fontFamily: family('ui', w), fontWeight: latin ? undefined : String(w) }),
      mono: (w = 400) => ({ fontFamily: latin ? FONTS.mono[w] || FONTS.mono[400] : Platform.select({ ios: 'Menlo', default: 'monospace' }) }),
    },
    shadow: (level = 'card') => {
      const spec = {
        hero: { y: 18, r: 20, o: scheme === 'dark' ? 0.6 : 0.16, e: 6 },
        card: { y: 12, r: 18, o: scheme === 'dark' ? 0.5 : 0.12, e: 4 },
        cta: { y: 8, r: 12, o: 0.35, e: 5, color: c.accent },
        sheet: { y: -10, r: 24, o: 0.25, e: 16 },
      }[level];
      return {
        shadowColor: spec.color || c.shadow, shadowOpacity: spec.o, shadowRadius: spec.r,
        shadowOffset: { width: 0, height: spec.y }, elevation: spec.e,
      };
    },
  };
}

export function useTheme() {
  const system = useColorScheme();
  const { prefs, lang } = usePrefs();
  const scheme = prefs.themeMode === 'system' ? (system === 'dark' ? 'dark' : 'light') : prefs.themeMode;
  return useMemo(() => buildTheme(scheme, lang), [scheme, lang]);
}
