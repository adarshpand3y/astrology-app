import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { useTrends } from '../../hooks/data';
import { useI18n } from '../../i18n';
import { useTheme } from '../../theme';
import { shortDate } from '../../utils/format';
import { Card, ErrorView, Loading, Rich, Row, T } from '../ui';

const RANGES = [14, 30, 90];
const MOOD_H = 64;      // mood strip height
const PRACTICE_H = 9;   // remedies strip height
const MOOD_STEPS = [0.3, 0.45, 0.62, 0.8, 1]; // rating 1–5: one hue, brighter = better day

/** 'all' | 'some' | 'none' (due but skipped) | null (nothing due). */
function practiceLevel({ done, due }) {
  if (!due && !done) return null;
  if (done >= due) return 'all';
  return done ? 'some' : 'none';
}

/**
 * Mood (from the daily log) and remedy practice over the last 14/30/90 days: two strips sharing one
 * day axis (no second scale), tap or drag across to read a day, plus the trends insights.
 */
export function MoodPractice() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const [days, setDays] = useState(30);
  const [width, setWidth] = useState(0);
  const [selected, setSelected] = useState(null);
  const { data, error, loading, refetch } = useTrends(days);
  const ratings = t('journal.ratings');
  const bars = data?.bars || [];
  const gap = days <= 14 ? 4 : days <= 30 ? 2 : 1;

  const practiceFill = (lv) => (lv === 'all' ? th.c.accent : lv === 'some' ? th.soft(0.45) : lv === 'none' ? th.c.track : 'transparent');
  const pickAt = (x) => {
    if (!width || !bars.length) return;
    const i = Math.max(0, Math.min(bars.length - 1, Math.floor((x / width) * bars.length)));
    setSelected(bars[i].date);
  };

  const sel = selected && bars.find((b) => b.date === selected);
  let caption = data?.average ? t('mood.avg', { v: data.average }) + ' · ' + t('mood.hint') : t('mood.hint');
  if (sel) {
    const date = shortDate(sel.date, lang);
    const mood = sel.rating ? ratings[sel.rating - 1] : t('mood.noLog');
    caption = sel.remedies.due || sel.remedies.done
      ? t('mood.day', { date, mood, done: sel.remedies.done, due: Math.max(sel.remedies.due, sel.remedies.done) })
      : t('mood.dayNoDue', { date, mood });
  }

  return (
    <Card radius={18} pad={16} style={{ marginTop: 14 }}>
      <Row style={{ justifyContent: 'space-between', marginBottom: 10 }}>
        <T v="eyebrow">{t('mood.title')}</T>
        <Row gap={4}>
          {RANGES.map((n) => {
            const active = n === days;
            return (
              <Pressable key={n} onPress={() => { setDays(n); setSelected(null); }} hitSlop={4}
                accessibilityRole="button" accessibilityState={{ selected: active }}
                style={{ paddingVertical: 4, paddingHorizontal: 9, borderRadius: 8, backgroundColor: active ? th.soft(0.12) : 'transparent' }}>
                <Text style={[th.font.ui(600), { fontSize: 11.5, color: active ? th.c.accentDark : th.c.ink3 }]}>{t('mood.range', { n })}</Text>
              </Pressable>
            );
          })}
        </Row>
      </Row>
      <T v="caption" style={{ marginBottom: 10, color: sel ? th.c.ink : th.c.ink3 }} numberOfLines={1}>{caption}</T>

      {loading && !data ? <Loading style={{ paddingVertical: 30 }} /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {bars.length ? (
        <>
          <T v="tiny" style={{ fontSize: 10, marginBottom: 4 }}>{t('mood.moodRow')}</T>
          <View
            onLayout={(e) => setWidth(e.nativeEvent.layout.width)}
            onStartShouldSetResponder={() => true}
            onResponderGrant={(e) => pickAt(e.nativeEvent.locationX)}
            onResponderMove={(e) => pickAt(e.nativeEvent.locationX)}
            onResponderTerminationRequest={() => true}
          >
            <View pointerEvents="none" style={{ flexDirection: 'row', alignItems: 'flex-end', gap, height: MOOD_H }}>
              {bars.map((b) => (
                <View key={b.date} style={{
                  flex: 1, borderRadius: days > 30 ? 1 : 3,
                  height: b.rating ? (b.rating / 5) * MOOD_H : 3,
                  backgroundColor: b.rating ? th.soft(MOOD_STEPS[b.rating - 1]) : th.c.track,
                  borderWidth: b.date === selected ? 1.5 : 0, borderColor: th.c.ink,
                }} />
              ))}
            </View>
            <View pointerEvents="none">
              <T v="tiny" style={{ fontSize: 10, marginTop: 10, marginBottom: 4 }}>{t('mood.practiceRow')}</T>
            </View>
            <View pointerEvents="none" style={{ flexDirection: 'row', gap, height: PRACTICE_H }}>
              {bars.map((b) => {
                const lv = practiceLevel(b.remedies);
                return (
                  <View key={b.date} style={{
                    flex: 1, borderRadius: 2, backgroundColor: practiceFill(lv),
                    borderWidth: b.date === selected ? 1.5 : lv ? 0 : 1, borderColor: b.date === selected ? th.c.ink : th.c.hair,
                  }} />
                );
              })}
            </View>
          </View>
          <Row style={{ justifyContent: 'space-between', marginTop: 6 }}>
            <T v="mono" style={{ fontSize: 9.5 }}>{shortDate(bars[0].date, lang)}</T>
            <T v="mono" style={{ fontSize: 9.5 }}>{shortDate(bars[bars.length - 1].date, lang)}</T>
          </Row>
          <Row gap={12} style={{ marginTop: 10, flexWrap: 'wrap' }}>
            {[['all', t('mood.all')], ['some', t('mood.some')], ['none', t('mood.none')]].map(([lv, label]) => (
              <Row key={lv} gap={5}>
                <View style={{ width: 10, height: 10, borderRadius: 2, backgroundColor: practiceFill(lv) }} />
                <T v="tiny" style={{ fontSize: 10.5 }}>{label}</T>
              </Row>
            ))}
          </Row>

          {data.insights.length ? (
            <View style={{ gap: 10, marginTop: 16 }}>
              {data.insights.map((ins) => {
                const k = th.kind[ins.kind];
                return (
                  <Row key={ins.text} gap={10} align="flex-start">
                    <View style={{ width: 26, height: 26, borderRadius: 13, backgroundColor: k.tint, alignItems: 'center', justifyContent: 'center' }}>
                      <Text style={{ color: k.solid, fontSize: 12 }}>{ins.glyph}</Text>
                    </View>
                    <Rich v="small" text={ins.text} style={{ flex: 1, fontSize: 12.5, lineHeight: 19 }} />
                  </Row>
                );
              })}
            </View>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}
