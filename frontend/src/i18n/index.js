import { useCallback, useMemo } from 'react';

import { brand } from '../config/env';
import { LANGUAGES, usePrefs } from '../state/PrefsContext';
import en from './en';
import hi from './hi';
import { term } from './terms';

const STRINGS = { en, hi };
export { LANGUAGES };
export const LANGUAGE_NAMES = { en: 'English', hi: 'हिन्दी' };

function lookup(lang, key) {
  const walk = (obj) => key.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
  return walk(STRINGS[lang]) ?? walk(en) ?? key;
}

/**
 * `t('auth.verifyHint', { email })`, `tr('graha', 'Me')` → "Budha" / "बुध".
 * `{app}` is always filled with the brand name.
 */
export function useI18n() {
  const { lang } = usePrefs();

  const t = useCallback((key, vars) => {
    const s = lookup(lang, key);
    if (typeof s !== 'string') return s;
    const all = { app: brand.name, ...vars };
    return s.replace(/\{(\w+)\}/g, (_, k) => (all[k] ?? `{${k}}`));
  }, [lang]);

  const tr = useCallback((category, value) => term(lang, category, value), [lang]);

  return useMemo(() => ({ t, tr, lang, locale: lang === 'hi' ? 'hi-IN' : 'en-IN' }), [t, tr, lang]);
}
