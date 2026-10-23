import { Pressable, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';

import { useI18n } from '../i18n';
import { useTheme } from '../theme';

const ICONS = {
  index: 'M3 9.5 11 3l8 6.5V19a1 1 0 0 1-1 1h-4v-6H8v6H4a1 1 0 0 1-1-1z',
  timeline: 'M11 3a8 8 0 1 0 0 16 8 8 0 0 0 0-16M11 6v5l3.5 2',
  chart: 'M11 2 20 11l-9 9-9-9zM11 2v18M2 11h18',
  remedies: 'M11 3c2 3 5 4.5 5 8a5 5 0 0 1-10 0c0-3.5 3-5 5-8z',
  profile: 'M11 3.9a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2M4.5 19c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6',
};
const LABELS = { index: 'tabs.home', timeline: 'tabs.timeline', chart: 'tabs.chart', remedies: 'tabs.remedies', profile: 'tabs.profile' };

/** The design's tab bar: 22px stroked line icons, 9.5px labels, frosted surface. */
export function TabBar({ state, navigation, hidden }) {
  const th = useTheme();
  const { t } = useI18n();
  const insets = useSafeAreaInsets();
  return (
    <View style={{
      flexDirection: 'row', justifyContent: 'space-around', backgroundColor: th.c.tabBg,
      borderTopWidth: 1, borderTopColor: th.c.hair, paddingTop: 9, paddingHorizontal: 12,
      paddingBottom: Math.max(insets.bottom, 12),
    }}>
      {state.routes.map((route, index) => {
        if (!ICONS[route.name] || hidden?.has(route.name)) return null;
        const focused = state.index === index;
        const color = focused ? th.c.accent : th.c.tabInactive;
        return (
          <Pressable
            key={route.key}
            accessibilityRole="tab"
            accessibilityState={{ selected: focused }}
            onPress={() => {
              const event = navigation.emit({ type: 'tabPress', target: route.key, canPreventDefault: true });
              if (!focused && !event.defaultPrevented) navigation.navigate(route.name);
            }}
            style={{ flex: 1, alignItems: 'center', gap: 4 }}
          >
            <Svg width={22} height={22} viewBox="0 0 22 22" fill="none" stroke={color} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
              <Path d={ICONS[route.name]} />
            </Svg>
            <Text style={[th.font.ui(600), { fontSize: 9.5, color }]}>{t(LABELS[route.name])}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
