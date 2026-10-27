import { MaterialCommunityIcons } from '@expo/vector-icons';

// Vector icons where text symbols (◐ ◷ ◔ …) drew at uneven sizes depending on the font.

/** Remedy kind → icon. */
const REMEDY_ICONS = {
  mantra: 'om', fast: 'food-off-outline', charity: 'hand-heart-outline', gem: 'diamond-stone', seva: 'cow',
  custom: 'star-four-points-outline',
};

/** Mood rating 1–5 (Heavy → Bright) → icon, a cloud through filling circles to the sun. */
export const MOOD_ICONS = ['weather-cloudy', 'circle-slice-2', 'circle-slice-4', 'circle-slice-6', 'white-balance-sunny'];

export function Icon({ name, size, color }) {
  return <MaterialCommunityIcons name={name} size={size} color={color} />;
}

export function RemedyIcon({ kind, size, color }) {
  return <Icon name={REMEDY_ICONS[kind] || REMEDY_ICONS.custom} size={size} color={color} />;
}
