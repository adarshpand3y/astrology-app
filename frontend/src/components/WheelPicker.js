import * as Haptics from 'expo-haptics';
import { useEffect, useRef } from 'react';
import { FlatList, Platform, Text, View } from 'react-native';

import { useTheme } from '../theme';

export const ITEM = 44;
const VISIBLE = 5; // odd, so one row sits in the centre band
const PAD = ITEM * ((VISIBLE - 1) / 2);

const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));

/**
 * One scroll wheel. `items` are display strings, `index` is the selected row
 * (controlled). Rows snap to the centre band; settling on a new row calls
 * onChange(index). If `index` changes from outside (e.g. day clamped when the
 * month changes) the wheel scrolls to it.
 */
export function Wheel({ items, index, onChange, flex = 1, align = 'center' }) {
  const th = useTheme();
  const list = useRef(null);
  const shown = useRef(index);

  useEffect(() => {
    if (shown.current === index) return;
    shown.current = index;
    list.current?.scrollToOffset({ offset: index * ITEM, animated: true });
  }, [index]);

  const settle = (y) => {
    const i = clamp(Math.round(y / ITEM), 0, items.length - 1);
    if (i === shown.current) return;
    shown.current = i;
    if (Platform.OS !== 'web') Haptics.selectionAsync().catch(() => {});
    onChange(i);
  };

  return (
    <View style={{ flex, height: ITEM * VISIBLE }}>
      <FlatList
        ref={list}
        data={items}
        extraData={index}
        keyExtractor={(_, i) => String(i)}
        getItemLayout={(_, i) => ({ length: ITEM, offset: ITEM * i, index: i })}
        initialScrollIndex={clamp(index, 0, items.length - 1)}
        snapToInterval={ITEM}
        decelerationRate="fast"
        showsVerticalScrollIndicator={false}
        nestedScrollEnabled
        contentContainerStyle={{ paddingVertical: PAD }}
        onMomentumScrollEnd={(e) => settle(e.nativeEvent.contentOffset.y)}
        onScrollEndDrag={(e) => {
          // A slow release produces no momentum on some devices: settle now.
          if (Math.abs(e.nativeEvent.velocity?.y || 0) < 0.05) settle(e.nativeEvent.contentOffset.y);
        }}
        renderItem={({ item, index: i }) => {
          const d = Math.abs(i - index);
          return (
            <View style={{ height: ITEM, justifyContent: 'center', paddingHorizontal: 6 }}>
              <Text
                numberOfLines={1}
                style={[
                  th.font.ui(d === 0 ? 600 : 400),
                  {
                    textAlign: align, fontSize: d === 0 ? 19 : 17,
                    color: d === 0 ? th.c.ink : th.c.ink3, opacity: d === 0 ? 1 : d === 1 ? 0.8 : 0.45,
                  },
                ]}
              >
                {item}
              </Text>
            </View>
          );
        }}
      />
    </View>
  );
}

/** Row of wheels sharing one highlighted centre band. */
export function WheelGroup({ children }) {
  const th = useTheme();
  return (
    <View style={{ height: ITEM * VISIBLE, flexDirection: 'row', gap: 4 }}>
      <View
        pointerEvents="none"
        style={{
          position: 'absolute', left: 0, right: 0, top: PAD, height: ITEM, borderRadius: 12,
          backgroundColor: th.soft(0.1), borderWidth: 1, borderColor: th.soft(0.22),
        }}
      />
      {children}
    </View>
  );
}
