import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { TimelineNav } from '../../../components/TimelineNav';
import { Card, ErrorView, Loading, Row, Screen, SoftPanel, T } from '../../../components/ui';
import { useVratCalendar } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { addMonths, dateLine, DAY_LETTERS, daysBetween, monthLabel, shortDate, todayISO } from '../../../utils/format';

/** "‹ November 2026 ›"; tapping the label returns to this month. */
function MonthPager({ month, onChange }) {
  const th = useTheme();
  const { lang } = useI18n();
  const arrow = (dir) => (
    <Pressable hitSlop={10} onPress={() => onChange(addMonths(month, dir))}>
      <Text style={{ fontSize: 15, color: th.c.ink2, paddingHorizontal: 2 }}>{dir < 0 ? '‹' : '›'}</Text>
    </Pressable>
  );
  return (
    <Row gap={10} style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair2, borderRadius: 11, paddingVertical: 6, paddingHorizontal: 11 }}>
      {arrow(-1)}
      <Pressable onPress={() => onChange(todayISO().slice(0, 7))}>
        <Text style={[th.font.ui(600), { fontSize: 12.5, color: th.c.ink, minWidth: 96, textAlign: 'center' }]}>{monthLabel(month, lang)}</Text>
      </Pressable>
      {arrow(1)}
    </Row>
  );
}

/** Monday-first month grid: date, the tithi within its paksha, and a dot for a fast (filled) or festival. */
function MonthGrid({ days, selected, onSelect }) {
  const th = useTheme();
  const { lang } = useI18n();
  const today = todayISO();
  const [y, m] = days[0].date.split('-').map(Number);
  const lead = (new Date(Date.UTC(y, m - 1, 1)).getUTCDay() + 6) % 7;
  const cells = [...Array(lead).fill(null), ...days];
  while (cells.length % 7) cells.push(null);
  const weeks = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

  return (
    <View>
      <Row gap={0} style={{ marginBottom: 6 }}>
        {DAY_LETTERS[lang].map((l, i) => (
          <Text key={i} style={[th.font.ui(600), { flex: 1, textAlign: 'center', fontSize: 10.5, color: th.c.ink3 }]}>{l}</Text>
        ))}
      </Row>
      {weeks.map((week, w) => (
        <Row key={w} gap={0}>
          {week.map((d, i) => {
            if (!d) return <View key={i} style={{ flex: 1, height: 52 }} />;
            const isSel = d.date === selected;
            const isToday = d.date === today;
            const fast = d.observances.some((o) => o.fast);
            return (
              <Pressable
                key={d.date}
                onPress={() => onSelect(d.date)}
                accessibilityRole="button"
                accessibilityLabel={[shortDate(d.date, lang), ...d.observances.map((o) => o.name)].join(', ')}
                style={{ flex: 1, height: 52, padding: 2 }}
              >
                <View style={{
                  flex: 1, borderRadius: 10, alignItems: 'center', justifyContent: 'center',
                  backgroundColor: isSel ? th.soft(0.18) : 'transparent',
                  borderWidth: isToday ? 1.5 : 0, borderColor: th.c.accent,
                }}>
                  <Text style={[th.font.ui(isSel || isToday ? 700 : 500), { fontSize: 14, color: th.c.ink }]}>{Number(d.date.slice(8))}</Text>
                  <Text style={[th.font.ui(500), { fontSize: 9, color: th.c.ink3 }]}>
                    {d.tithi > 15 ? d.tithi - 15 : d.tithi}{d.paksha === 'Shukla' ? '◑' : '◐'}
                  </Text>
                  <View style={{
                    marginTop: 2, width: 5, height: 5, borderRadius: 3,
                    backgroundColor: d.observances.length ? (fast ? th.c.accent : 'transparent') : 'transparent',
                    borderWidth: d.observances.length && !fast ? 1 : 0, borderColor: th.c.accent,
                  }} />
                </View>
              </Pressable>
            );
          })}
        </Row>
      ))}
    </View>
  );
}

/** One Ekadashi or festival: glyph, name, date, a "Fast" tag and its summary, or with `detailed`,
 * the numbered steps of what to do. */
function ObservanceRow({ o, date, first, detailed, badge, next, dim }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  return (
    <Row gap={12} align="flex-start" style={{
      paddingVertical: 13, borderTopWidth: first || next ? 0 : 1, borderTopColor: th.c.hair, opacity: dim ? 0.55 : 1,
      ...(next ? { backgroundColor: th.soft(0.1), borderRadius: 14, marginHorizontal: -10, paddingHorizontal: 10, marginTop: 8 } : null),
    }}>
      <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ fontSize: 16, color: th.c.accent }}>{o.glyph}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Row gap={8} style={{ flexWrap: 'wrap' }}>
          <T weight={600} style={{ fontSize: 14.5 }}>{o.name}</T>
          {badge ? (
            <View style={{ paddingVertical: 1, paddingHorizontal: 7, borderRadius: 20, backgroundColor: next ? th.c.accent : th.c.muted }}>
              <Text style={[th.font.ui(600), { fontSize: 10, color: next ? th.c.onAccent : th.c.ink2 }]}>{badge}</Text>
            </View>
          ) : null}
          {o.fast ? (
            <View style={{ paddingVertical: 1, paddingHorizontal: 7, borderRadius: 20, backgroundColor: th.soft(0.12) }}>
              <Text style={[th.font.ui(600), { fontSize: 10, color: th.c.accentDark }]}>{t('calendar.fast')}</Text>
            </View>
          ) : null}
        </Row>
        {date ? <T v="caption" style={{ marginTop: 2 }}>{dateLine(date, lang)}</T> : null}
        <T v="small" style={{ marginTop: 4, fontSize: 12.5, lineHeight: 19, color: th.c.ink2 }}>{o.how}</T>
        {detailed && o.steps?.length ? (
          <View style={{ marginTop: 10 }}>
            <T v="eyebrow" style={{ marginBottom: 6 }}>{t('calendar.whatToDo')}</T>
            {o.steps.map((s, i) => (
              <Row key={i} gap={9} align="flex-start" style={{ marginBottom: 6 }}>
                <View style={{ width: 18, height: 18, borderRadius: 9, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center', marginTop: 1 }}>
                  <Text style={[th.font.ui(700), { fontSize: 10, color: th.c.accentDark }]}>{i + 1}</Text>
                </View>
                <T v="small" style={{ flex: 1, fontSize: 13, lineHeight: 19.5, color: th.c.ink }}>{s}</T>
              </Row>
            ))}
          </View>
        ) : null}
      </View>
    </Row>
  );
}

export default function FestivalCalendar() {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const [month, setMonth] = useState(todayISO().slice(0, 7));
  const [selected, setSelected] = useState(todayISO());
  const [showEarlier, setShowEarlier] = useState(false);
  const { data, error, loading, refreshing, refetch } = useVratCalendar(month);

  const changeMonth = (m) => {
    setMonth(m);
    setShowEarlier(false);
    setSelected(m === todayISO().slice(0, 7) ? todayISO() : `${m}-01`);
  };
  const day = data?.days.find((d) => d.date === selected);
  const all = data ? data.days.flatMap((d) => d.observances.map((o) => ({ o, date: d.date }))) : [];
  // Upcoming first (nearest highlighted, with how soon), then the month's earlier ones, folded away.
  const today = todayISO();
  const upcoming = all.filter((x) => x.date >= today);
  const past = all.filter((x) => x.date < today);
  const soon = (date) => {
    const n = daysBetween(today, date);
    return n === 0 ? t('calendar.today') : n === 1 ? t('calendar.tomorrow') : n <= 30 ? t('calendar.inDays', { n }) : null;
  };
  const showPast = showEarlier || !upcoming.length;

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <Row style={{ justifyContent: 'space-between', paddingHorizontal: 2, paddingTop: 8, paddingBottom: 16 }}>
        <T v="screenTitle" style={{ flexShrink: 1 }} numberOfLines={1}>{t('calendar.title')}</T>
        <MonthPager month={month} onChange={changeMonth} />
      </Row>
      <TimelineNav current="calendar" />
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <>
          <Card pad={12} shadow>
            <MonthGrid days={data.days} selected={selected} onSelect={setSelected} />
          </Card>

          {day ? (
            <SoftPanel style={{ marginTop: 14 }}>
              <T v="eyebrow" style={{ color: th.c.accentDark }}>
                {dateLine(day.date, lang)} · {day.is_adhika ? `${t('panchang.adhika')} ` : ''}{tr('month', day.month)}
              </T>
              <T style={{ fontSize: 14, marginTop: 4 }}>
                {t('calendar.tithi', { paksha: tr('paksha', day.paksha), tithi: tr('tithi', day.tithi_name) })}
              </T>
              {day.observances.length
                ? day.observances.map((o, i) => <ObservanceRow key={o.key} o={o} first={i === 0} detailed />)
                : <T v="small" style={{ marginTop: 6, color: th.c.ink2 }}>{t('calendar.noneDay')}</T>}
            </SoftPanel>
          ) : null}

          <T v="eyebrow" style={{ marginTop: 22, marginBottom: 4, paddingHorizontal: 2 }}>
            {upcoming.length && past.length ? t('calendar.comingUp') : t('calendar.thisMonth')}
          </T>
          <Card pad={16} style={{ paddingVertical: 4 }}>
            {!all.length ? <T v="small" style={{ paddingVertical: 14, color: th.c.ink2 }}>{t('calendar.none')}</T> : null}
            {upcoming.map(({ o, date }, i) => (
              <Pressable key={`${date}:${o.key}`} onPress={() => setSelected(date)}>
                <ObservanceRow o={o} date={date} first={i === 0} badge={soon(date)}
                  next={date === upcoming[0].date} />
              </Pressable>
            ))}
            {upcoming.length && past.length ? (
              <Pressable onPress={() => setShowEarlier((v) => !v)} hitSlop={6}
                style={{ paddingVertical: 12, borderTopWidth: 1, borderTopColor: th.c.hair }}>
                <T v="small" weight={600} style={{ color: th.c.accentDark }}>
                  {showEarlier ? t('calendar.hideEarlier') : t('calendar.showEarlier', { n: past.length })}
                </T>
              </Pressable>
            ) : null}
            {showPast ? past.map(({ o, date }, i) => (
              <Pressable key={`${date}:${o.key}`} onPress={() => setSelected(date)}>
                <ObservanceRow o={o} date={date} first={i === 0 && !upcoming.length} dim={upcoming.length > 0} />
              </Pressable>
            )) : null}
          </Card>
          <T v="tiny" style={{ marginTop: 12, paddingHorizontal: 4, lineHeight: 16 }}>{t('calendar.note')}</T>
        </>
      ) : null}
    </Screen>
  );
}
