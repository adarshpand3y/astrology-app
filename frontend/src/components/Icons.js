import { MaterialCommunityIcons } from '@expo/vector-icons';

import { useTheme } from '../theme';

// Vector icons where text symbols (◐ ◷ ◔ …) drew at uneven sizes depending on the font.

/** Remedy kind → icon. */
const REMEDY_ICONS = {
  mantra: 'om', fast: 'food-off-outline', charity: 'hand-heart-outline', gem: 'diamond-stone', seva: 'cow',
  puja: 'candle', element: 'yin-yang', custom: 'star-four-points-outline',
};
/** Lagna element (tattva) practice → icon. */
const ELEMENT_ICONS = { fire: 'fire', earth: 'sprout', air: 'weather-windy', water: 'water' };

/** Mood rating 1–5 (Heavy → Bright) → icon, a cloud through filling circles to the sun. */
export const MOOD_ICONS = ['weather-cloudy', 'circle-slice-2', 'circle-slice-4', 'circle-slice-6', 'white-balance-sunny'];

export function Icon({ name, size, color }) {
  return <MaterialCommunityIcons name={name} size={size} color={color} />;
}

/** The Pro mark: a crown, in the accent colour unless told otherwise. It is a Text underneath, so
 * it also sits inline inside a <Text>. */
export function ProIcon({ size = 12, color }) {
  const th = useTheme();
  return <Icon name="crown" size={size} color={color || th.c.accent} />;
}

export function RemedyIcon({ kind, element, size, color }) {
  const name = (kind === 'element' && ELEMENT_ICONS[element]) || REMEDY_ICONS[kind] || REMEDY_ICONS.custom;
  return <Icon name={name} size={size} color={color} />;
}
