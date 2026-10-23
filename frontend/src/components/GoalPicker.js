import { Pressable, Text, View } from 'react-native';

import { useTheme } from '../theme';
import { T } from './ui';

/**
 * Grid of goal cards (catalogue from GET /remedies/goals/). Multi-select, capped at `max`;
 * `onLimit` fires when the user tries to pick one more. With `max` 1 (free plan) it is
 * single-select: tapping another goal swaps it in.
 */
export function GoalPicker({ catalogue, value, onChange, max = 3, onLimit }) {
  const th = useTheme();
  const toggle = (key) => {
    if (value.includes(key)) onChange(value.filter((k) => k !== key));
    else if (max === 1) onChange([key]);
    else if (value.length >= max) onLimit?.();
    else onChange([...value, key]);
  };
  return (
    <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 10 }}>
      {catalogue.map((g) => {
        const active = value.includes(g.key);
        return (
          <Pressable
            key={g.key}
            accessibilityRole={max === 1 ? 'radio' : 'checkbox'}
            accessibilityState={{ checked: active }}
            onPress={() => toggle(g.key)}
            style={({ pressed }) => ({
              flexBasis: '47%', flexGrow: 1, minHeight: 112, padding: 13, borderRadius: 16, borderWidth: 1.5,
              borderColor: active ? th.c.accent : th.c.hair, backgroundColor: active ? th.soft(0.08) : th.c.surface,
              opacity: pressed ? 0.85 : 1,
            })}
          >
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: active ? th.c.accent : th.soft(0.13), alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ fontSize: 16, color: active ? th.c.onAccent : th.c.accent }}>{g.glyph}</Text>
              </View>
              {active && max > 1 ? (
                <View style={{ width: 20, height: 20, borderRadius: 10, backgroundColor: th.c.accent, alignItems: 'center', justifyContent: 'center' }}>
                  <Text style={[th.font.ui(700), { fontSize: 11, color: th.c.onAccent }]}>{value.indexOf(g.key) + 1}</Text>
                </View>
              ) : null}
            </View>
            {active && max === 1 ? (
              <View style={{ position: 'absolute', top: 13, right: 13, width: 20, height: 20, borderRadius: 10, backgroundColor: th.c.accent, alignItems: 'center', justifyContent: 'center' }}>
                <Text style={[th.font.ui(700), { fontSize: 11, color: th.c.onAccent }]}>✓</Text>
              </View>
            ) : null}
            <T weight={600} style={{ fontSize: 14, marginTop: 10 }}>{g.label}</T>
            <T v="caption" style={{ marginTop: 2, lineHeight: 15 }}>{g.blurb}</T>
          </Pressable>
        );
      })}
    </View>
  );
}
