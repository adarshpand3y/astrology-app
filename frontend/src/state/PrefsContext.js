import AsyncStorage from '@react-native-async-storage/async-storage';
import { getLocales } from 'expo-localization';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { brand } from '../config/env';

const STORAGE_KEY = 'prefs.v2';
export const LANGUAGES = brand.features.hindi ? ['en', 'hi'] : ['en'];

const DEFAULTS = {
  language: brand.defaults.language,
  themeMode: brand.defaults.themeMode,
  chartStyle: brand.defaults.chartStyle,
};

function resolveLanguage(pref) {
  if (pref !== 'system' && LANGUAGES.includes(pref)) return pref;
  const code = getLocales()?.[0]?.languageCode;
  return LANGUAGES.includes(code) ? code : 'en';
}

const PrefsContext = createContext(null);

export function PrefsProvider({ children }) {
  const [prefs, setPrefs] = useState(DEFAULTS);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => { if (raw) setPrefs({ ...DEFAULTS, ...JSON.parse(raw) }); })
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);

  const update = useCallback((patch) => {
    setPrefs((prev) => {
      const next = { ...prev, ...patch };
      AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, []);

  const lang = resolveLanguage(prefs.language);
  const value = useMemo(() => ({ prefs, ready, update, lang }), [prefs, ready, update, lang]);
  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
}

export function usePrefs() {
  const ctx = useContext(PrefsContext);
  if (!ctx) throw new Error('usePrefs must be used inside PrefsProvider');
  return ctx;
}
