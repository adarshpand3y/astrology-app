import { useFocusEffect } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Text, View } from 'react-native';

import { DatePager, TimelineNav } from '../../../components/TimelineNav';
import { ErrorView, Loading, Row, SCREEN_TOP_PAD, Screen, T } from '../../../components/ui';
import { useTimeline } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { clock, range, shortDate, todayISO } from '../../../utils/format';

export default function DayTimeline() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const [date, setDate] = useState(todayISO());
  const { data, error, loading, refreshing, refetch } = useTimeline(date);
  const [now, setNow] = useState(() => Date.now());

  const isNowBlock = (b) => b.end && Date.parse(b.start) <= now && now < Date.parse(b.end) && b.category !== 'kaal';
  const nowBlock = data?.blocks.find(isNowBlock);
  const nowKey = nowBlock ? `${nowBlock.key}-${nowBlock.start}` : null;

  // Open on the current period: scroll it to the top whenever the tab is opened or the date
  // changes (not on pull-to-refresh). Layout positions arrive via onLayout, so retry as they do.
  const scrollRef = useRef(null);
  const listY = useRef(null);
  const blockY = useRef({});
  const pendingScroll = useRef(true);
  const scrollToNow = useCallback(() => {
    const y = nowKey && blockY.current[nowKey];
    if (!pendingScroll.current || listY.current == null || y == null) return;
    pendingScroll.current = false;
    scrollRef.current?.scrollTo({ y: Math.max(0, SCREEN_TOP_PAD + listY.current + y - 8), animated: false });
  }, [nowKey]);

  useFocusEffect(useCallback(() => {
    setNow(Date.now()); // the "now" card moves on while the tab sits in the background
    pendingScroll.current = true;
  }, []));
  useEffect(() => { pendingScroll.current = true; }, [date]);
  useEffect(() => { scrollToNow(); }, [scrollToNow, now]);

  return (
    <Screen refreshing={refreshing} onRefresh={refetch} scrollRef={scrollRef}>
      <Row style={{ justifyContent: 'space-between', paddingHorizontal: 2, paddingTop: 8, paddingBottom: 4 }}>
        <T v="screenTitle">{t('timeline.title')}</T>
        <DatePager date={date} onChange={setDate} />
      </Row>
      {data ? (
        <T v="small" style={{ fontSize: 12, paddingHorizontal: 2, paddingBottom: 14 }}>
          {t('timeline.meta', {
            date: shortDate(data.date, lang, true), city: data.location.city,
            sr: clock(data.sunrise, lang), ss: clock(data.sunset, lang),
          })}
        </T>
      ) : null}
      <TimelineNav current="index" />

      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <View style={{ paddingLeft: 6 }} onLayout={(e) => { listY.current = e.nativeEvent.layout.y; scrollToNow(); }}>
          {data.blocks.map((b, i) => {
            const k = th.kind[b.kind];
            const nightStart = b.part === 'night' && data.blocks[i - 1]?.part !== 'night';
            const id = `${b.key}-${b.start}`;
            const isNow = id === nowKey;
            return (
              <View key={id} onLayout={(e) => { blockY.current[id] = e.nativeEvent.layout.y; if (isNow) scrollToNow(); }}>
                {nightStart ? <T v="eyebrow" style={{ marginLeft: 65, marginTop: 8, marginBottom: 10 }}>{t('timeline.night')}</T> : null}
                <View style={{ flexDirection: 'row', gap: 13, alignItems: 'stretch', marginBottom: 3 }}>
                  <View style={{ width: 52, alignItems: 'flex-end', paddingTop: 2 }}>
                    <T v="mono" style={{ color: k.solid }}>{clock(b.start, lang)}</T>
                    {isNow ? <T v="eyebrow" style={{ fontSize: 8.5, color: th.c.accent, marginTop: 2 }}>{t('timeline.nowLabel')}</T> : null}
                  </View>
                  <View style={{ width: 12, alignItems: 'center' }}>
                    <View style={{ width: 11, height: 11, borderRadius: 6, backgroundColor: k.solid, marginTop: 3, borderWidth: 2, borderColor: k.tint }} />
                    <View style={{ flex: 1, width: 2, backgroundColor: th.c.hair }} />
                  </View>
                  <View style={{
                    flex: 1, backgroundColor: k.tint, borderRadius: 14, paddingVertical: 12, paddingHorizontal: 14, marginBottom: 9,
                    borderWidth: isNow ? 1 : 0, borderColor: th.c.accent,
                  }}>
                    <Row style={{ justifyContent: 'space-between' }} align="flex-start">
                      <T weight={600} style={{ fontSize: 14.5, flex: 1 }}>{b.name}</T>
                      <View style={{ backgroundColor: k.tint, borderWidth: 1, borderColor: `${k.solid}33`, borderRadius: 20, paddingVertical: 3, paddingHorizontal: 8 }}>
                        <Text style={[th.font.ui(600), { fontSize: 10, color: k.solid }]}>{b.kind_label}</Text>
                      </View>
                    </Row>
                    <T v="caption" style={{ marginTop: 3 }}>{b.gloss}</T>
                    <T v="mono" style={{ fontSize: 10.5, marginTop: 6 }}>{range(b.start, b.end, lang)}</T>
                  </View>
                </View>
              </View>
            );
          })}
        </View>
      ) : null}
    </Screen>
  );
}
