import { useMemo, useRef, useState } from 'react';
import { Pressable, ScrollView, useWindowDimensions, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop, Text as SvgText } from 'react-native-svg';

import { useI18n } from '../../i18n';
import { useTheme } from '../../theme';
import { MONTHS, parts, shortDate } from '../../utils/format';
import { Row, T } from '../ui';

const GAP = 2;          // surface gap between cells
const MIN_CELL = 12;    // keeps cells tappable; narrower screens scroll sideways
const MAX_CELL = 16;
const LABEL_W = 30;     // weekday labels (pinned, outside the scroll area)
const FADE_W = 12;      // left-edge fade while scrolled
const TOP = 16;         // month labels
const STEPS = [0.26, 0.5, 0.75, 1]; // one hue (the accent), more done = stronger

/** 0 = nothing due / nothing done, 1-4 = share of the day's due remedies completed. */
export function level(done, due) {
  if (!done) return 0;
  const f = done / Math.max(due, 1);
  return f >= 1 ? 4 : f > 2 / 3 ? 3 : f > 1 / 3 ? 2 : 1;
}

/**
 * Small, label-free heatmap of the last `weeks` weeks (newest on the right) for summary cards.
 * Same levels and colours as the full heatmap; not interactive (the card around it is).
 */
export function MiniHeatmap({ days, weeks = 13, cell = 8, gap = 2 }) {
  const th = useTheme();
  const { t } = useI18n();
  if (!days?.length) return <View style={{ width: weeks * (cell + gap) - gap, height: 7 * (cell + gap) - gap }} />;
  const last = days[days.length - 1];
  const lastRow = parts(last.date).wd; // Sunday = 0
  const shown = days.slice(-((weeks - 1) * 7 + lastRow + 1)); // whole weeks, ending today
  const lead = parts(shown[0].date).wd;
  const step = cell + gap;
  const fill = (lv) => (lv === 0 ? th.c.track : th.soft(STEPS[lv - 1]));
  return (
    <Svg width={weeks * step - gap} height={7 * step - gap} accessibilityLabel={t('remedies.heatTitle')}>
      {shown.map((d, i) => (
        <Rect key={d.date} x={Math.floor((lead + i) / 7) * step} y={((lead + i) % 7) * step}
          width={cell} height={cell} rx={2} fill={fill(level(d.done, d.due))} />
      ))}
    </Svg>
  );
}

/**
 * Calendar heatmap of remedies done vs due. `days` = [{date, done, due}] oldest → newest
 * (GET /remedies/history/). Columns are weeks (Sunday on top), newest week on the right.
 */
export function Heatmap({ days, inset = 72 }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  // Start from an estimate (window minus screen gutters and card padding = `inset`) so the grid
  // draws on the first frame; onLayout corrects it if the real width differs.
  const { width: windowW } = useWindowDimensions();
  const [measured, setMeasured] = useState(0);
  const width = measured || Math.max(0, windowW - inset);
  const [selected, setSelected] = useState(null);
  const [scrolledIn, setScrolledIn] = useState(false); // scrolled away from the oldest week
  const scroller = useRef(null);
  const userScrolled = useRef(false);
  const weekdayNames = t('remedies.weekdays');

  const grid = useMemo(() => {
    const lead = parts(days[0]?.date)?.wd ?? 0; // Sunday = 0
    const cells = days.map((d, i) => ({ ...d, col: Math.floor((lead + i) / 7), row: (lead + i) % 7, lv: level(d.done, d.due) }));
    const cols = cells.length ? cells[cells.length - 1].col + 1 : 0;
    const byPos = new Map(cells.map((c) => [`${c.col}:${c.row}`, c]));
    const months = [];
    let prev = null;
    for (const c of cells) {
      const mo = parts(c.date).mo;
      if (c.row === 0 || c === cells[0]) {
        if (mo !== prev) months.push({ col: c.col, label: MONTHS[lang][mo - 1] });
        prev = mo;
      }
    }
    // Drop a month label that would collide with the next one (the partial first week).
    return { cells, cols, byPos, months: months.filter((m, i) => !months[i + 1] || months[i + 1].col - m.col >= 3) };
  }, [days, lang]);

  const gridW = width - LABEL_W; // the weekday column stays pinned; only the grid scrolls
  const cell = Math.max(MIN_CELL, Math.min(MAX_CELL, Math.floor(gridW / Math.max(grid.cols, 1)) - GAP));
  const step = cell + GAP;
  const svgW = grid.cols * step;
  const svgH = TOP + 7 * step;
  const scrolls = svgW > gridW;
  const sel = selected && grid.cells.find((c) => c.date === selected);
  const labelFont = { fontSize: 9, fill: th.c.ink3, fontFamily: th.font.ui(500).fontFamily };
  // eslint-disable-next-line react-hooks/exhaustive-deps -- keyed on the colours, not the theme object
  const fills = useMemo(() => [th.c.track, ...STEPS.map((o) => th.soft(o))], [th.c.track, th.c.accent]);

  // The 365 squares only change with the data, size or theme — not when a day is selected.
  // One tap handler on the grid (not one per square) keeps them cheap to draw.
  const squares = useMemo(() => grid.cells.map((c) => (
    <Rect key={c.date} x={c.col * step} y={TOP + c.row * step} width={cell} height={cell} rx={2.5} fill={fills[c.lv]} />
  )), [grid, step, cell, fills]);

  const tap = (e) => {
    const { locationX: x, locationY: y } = e.nativeEvent;
    const c = grid.byPos.get(`${Math.floor(x / step)}:${Math.floor((y - TOP) / step)}`);
    if (c && y >= TOP) setSelected((cur) => (cur === c.date ? null : c.date));
  };

  const caption = sel
    ? (sel.due ? t('remedies.heatDone', { date: shortDate(sel.date, lang), done: sel.done, due: sel.due })
      : t('remedies.heatNone', { date: shortDate(sel.date, lang) }))
    : t('remedies.heatTap');

  return (
    <View onLayout={(e) => {
      const w = e.nativeEvent.layout.width;
      setMeasured(w);
      // Pre-rendered while hidden (width 0): jump to the current week once it is shown.
      if (w > 0 && !userScrolled.current) requestAnimationFrame(() => scroller.current?.scrollToEnd({ animated: false }));
    }}>
      <T v="caption" style={{ marginBottom: 8, color: sel ? th.c.ink : th.c.ink3 }} accessibilityLiveRegion="polite">{caption}</T>
      <View style={{ flexDirection: 'row' }}>
        <Svg width={LABEL_W} height={svgH}>
          {[1, 3, 5].map((r) => (
            <SvgText key={r} x={0} y={TOP + r * step + cell - 2} {...labelFont}>{weekdayNames[r]}</SvgText>
          ))}
        </Svg>
        <View style={{ flex: 1 }}>
          <ScrollView
            ref={scroller}
            horizontal
            showsHorizontalScrollIndicator={false}
            scrollEnabled={scrolls}
            scrollEventThrottle={16}
            onScrollBeginDrag={() => { userScrolled.current = true; }}
            onScroll={(e) => setScrolledIn(e.nativeEvent.contentOffset.x > 1)}
            onContentSizeChange={(w) => {
              scroller.current?.scrollToEnd({ animated: false }); // open on the current week
              setScrolledIn(w > gridW + 1); // scrollToEnd doesn't always emit onScroll
            }}
          >
            <Pressable onPress={tap} accessibilityLabel={t('remedies.heatTitle')}>
              <Svg width={svgW} height={svgH} pointerEvents="none">
                {grid.months.map((m) => (
                  <SvgText key={`${m.col}-${m.label}`} x={m.col * step} y={10} {...labelFont}>{m.label}</SvgText>
                ))}
                {squares}
                {sel ? (
                  <Rect x={sel.col * step} y={TOP + sel.row * step} width={cell} height={cell} rx={2.5}
                    fill="none" stroke={th.c.ink} strokeWidth={1.5} />
                ) : null}
              </Svg>
            </Pressable>
          </ScrollView>
          {scrolls && scrolledIn ? (
            // Fade at the left edge: there are earlier weeks to scroll back to.
            <Svg pointerEvents="none" width={FADE_W} height={svgH} style={{ position: 'absolute', left: 0, top: 0 }}>
              <Defs>
                <LinearGradient id="heatFade" x1="0" y1="0" x2="1" y2="0">
                  <Stop offset="0" stopColor={th.c.surface} stopOpacity={1} />
                  <Stop offset="1" stopColor={th.c.surface} stopOpacity={0} />
                </LinearGradient>
              </Defs>
              <Rect x={0} y={0} width={FADE_W} height={svgH} fill="url(#heatFade)" />
            </Svg>
          ) : null}
        </View>
      </View>
      <Row gap={4} style={{ marginTop: 8 }}>
        {/* Only when there are earlier weeks off-screen to the left. */}
        <T v="tiny" style={{ flex: 1, fontSize: 10, color: th.c.ink3 }} numberOfLines={1}>
          {scrolls && scrolledIn ? `‹ ${t('remedies.heatSwipe')}` : ''}
        </T>
        <T v="tiny" style={{ fontSize: 10, marginRight: 2 }}>{t('remedies.heatLess')}</T>
        {fills.map((f, lv) => (
          <View key={lv} style={{ width: 11, height: 11, borderRadius: 2.5, backgroundColor: f }} />
        ))}
        <T v="tiny" style={{ fontSize: 10, marginLeft: 2 }}>{t('remedies.heatMore')}</T>
      </Row>
    </View>
  );
}
