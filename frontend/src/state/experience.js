import { useMemo } from 'react';

import { useAuth } from './AuthContext';

/** How much astrology the user knows (stored on the account). Lower levels see less detail. */
export const LEVELS = ['none', 'beginner', 'intermediate', 'advanced'];

// The lowest level (index into LEVELS) that sees each piece of the app. Adjust here only.
const MIN_LEVEL = {
  insightWhyOpen: 2, // Home insight's "Why" panel starts open
  skyNow: 1, // Home: planetary transits section
  skyDetail: 2, // Transits: degrees + pada, Gandmool filter, transit chart and lagna toggle
  vargas: 2, // Chart: D9 and the D2–D60 strip
  strength: 1, // Chart: Shadbala / Bhavabala screen
  strengthDetail: 3, // Strength: six-source virupas, Bhavabala components
  detailsDeep: 3, // Birth details: expanded planet fields, maitri matrix, Avakhada
  advancedAlerts: 2, // Alerts: transit and Sade Sati
};

// How many dasha levels (MD, AD, PD, SD, Prana) each experience level sees.
const DASHA_DEPTH = [2, 2, 3, 5];

/** `show(key)` says whether the user's level sees that part; `dashaDepth` caps the dasha chain. */
export function useExperience() {
  const { user } = useAuth();
  const raw = user?.experience;
  // Unset (old cached user, or before the question) behaves like the full app.
  const idx = LEVELS.includes(raw) ? LEVELS.indexOf(raw) : LEVELS.length - 1;
  return useMemo(() => ({
    level: LEVELS[idx],
    show: (key) => idx >= (MIN_LEVEL[key] ?? 0),
    dashaDepth: DASHA_DEPTH[idx],
  }), [idx]);
}
