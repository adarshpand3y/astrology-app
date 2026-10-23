import { useState } from 'react';
import { Text, View } from 'react-native';

import { DatePager, TimelineNav } from '../../../components/TimelineNav';
import { Card, ErrorView, Loading, Rich, Row, Screen, SoftPanel, T } from '../../../components/ui';
import { usePanchang } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { clock, todayISO } from '../../../utils/format';

export default function Panchang() {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const [date, setDate] = useState(todayISO());
  const { data, error, loading, refreshing, refetch } = usePanchang(date);

  const value = (r) => {
    if (r.key === 'tithi') return `${tr('paksha', r.paksha)} ${tr('tithi', r.name)}`;
    if (r.key === 'vara') return tr('weekday', r.name);
    if (r.key === 'nakshatra') return tr('nakshatra', r.name);
    if (r.key === 'yoga') return tr('yoga', r.name);
    return tr('karana', r.name);
  };

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <Row style={{ justifyContent: 'space-between', paddingHorizontal: 2, paddingTop: 8, paddingBottom: 16 }}>
        <T v="screenTitle">{t('panchang.title')}</T>
        <DatePager date={date} onChange={setDate} />
      </Row>
      <TimelineNav current="panchang" />
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <>
          <Card pad={0} shadow style={{ overflow: 'hidden' }}>
            <View style={{ backgroundColor: th.soft(0.15), paddingVertical: 15, paddingHorizontal: 18, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
              <View style={{ flex: 1 }}>
                <T v="eyebrow" style={{ color: th.c.accentDark, opacity: 0.85 }}>
                  {data.location.city} · {Math.abs(data.location.latitude).toFixed(2)}°{data.location.latitude >= 0 ? 'N' : 'S'}
                </T>
                <Text style={[th.font.display(400), { fontSize: 19, color: th.c.ink, marginTop: 2 }]}>
                  {t('panchang.shaka', { y: data.shaka_year, month: `${data.is_adhika ? `${t('panchang.adhika')} ` : ''}${tr('month', data.month)}` })}
                </Text>
              </View>
              <View style={{ alignItems: 'flex-end' }}>
                <T v="tiny" style={{ color: th.c.ink2, lineHeight: 18 }}>☀ {clock(data.sunrise, lang)} → {clock(data.sunset, lang)}</T>
                {data.moonrise ? <T v="tiny" style={{ color: th.c.ink2, lineHeight: 18 }}>☽ {t('panchang.rises', { t: clock(data.moonrise, lang, true) })}</T> : null}
              </View>
            </View>
            {data.rows.map((r) => (
              <Row key={r.key} gap={13} style={{ paddingVertical: 15, paddingHorizontal: 18, borderTopWidth: 1, borderTopColor: th.c.hair }}>
                <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: th.kind[r.kind].solid }} />
                <View style={{ width: 82 }}>
                  <T weight={600} style={{ fontSize: 14 }}>{t(`panchang.${r.key}`)}</T>
                  {t(`panchang.${r.key}Gloss`) ? <T v="tiny" style={{ fontSize: 10 }}>{t(`panchang.${r.key}Gloss`)}</T> : null}
                </View>
                <View style={{ flex: 1 }}>
                  <T style={{ fontSize: 14 }}>{value(r)}{r.pada ? ` · ${t('panchang.pada', { n: r.pada })}` : ''}</T>
                  <T v="tiny" style={{ color: th.c.ink2 }}>
                    {r.detail}{r.end ? ` · ${t('panchang.until', { t: clock(r.end, lang, true) })}` : ''}
                  </T>
                </View>
              </Row>
            ))}
          </Card>
          <SoftPanel style={{ marginTop: 14, borderRadius: 16, paddingVertical: 14, paddingHorizontal: 16, flexDirection: 'row', gap: 11 }}>
            <Text style={{ color: th.c.accent, fontSize: 14, marginTop: 1 }}>◈</Text>
            <Rich v="small" text={data.note} style={{ flex: 1, fontSize: 12, lineHeight: 18.5 }} />
          </SoftPanel>
        </>
      ) : null}
    </Screen>
  );
}
