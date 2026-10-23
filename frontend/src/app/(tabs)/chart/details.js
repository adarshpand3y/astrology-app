import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { BackLink, Card, ErrorView, GlyphDot, Loading, Row, Screen, Seg, T, Tag } from '../../../components/ui';
import { useAccount, useChart } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { clock, num, range } from '../../../utils/format';

const GOOD = ['exalted', 'moolatrikona', 'own', 'great_friend', 'friend'];
const BAD = ['debilitated', 'enemy', 'great_enemy'];

function KV({ rows }) {
  const th = useTheme();
  return rows.map(([k, v], i) => (
    <Row key={k} gap={12} align="flex-start" style={{ paddingVertical: 11, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
      <T v="small" style={{ width: 120 }}>{k}</T>
      <View style={{ flex: 1 }}>{typeof v === 'string' ? <T style={{ fontSize: 13.5 }}>{v}</T> : v}</View>
    </Row>
  ));
}

export default function BirthDetails() {
  const { t } = useI18n();
  const { profileId } = useAccount();
  const { data, error, loading, refreshing, refetch } = useChart(profileId);
  const [tab, setTab] = useState('planets');
  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <BackLink label={t('chart.title')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 14 }}>{t('details.title')}</T>
      <Seg options={[{ value: 'planets', label: t('details.planets') }, { value: 'panchang', label: t('panchang.title') },
        { value: 'avakhada', label: t('details.avakhada') }]} value={tab} onChange={setTab} style={{ marginBottom: 16 }} />
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data && tab === 'planets' ? <Planets chart={data} /> : null}
      {data && tab === 'panchang' ? <BirthPanchang chart={data} /> : null}
      {data && tab === 'avakhada' ? <Avakhada chart={data} /> : null}
    </Screen>
  );
}

function Planets({ chart }) {
  const th = useTheme();
  const { t, tr } = useI18n();
  const [open, setOpen] = useState(null);
  const l = chart.lagna;
  const rel = chart.relationships;
  const codes = Object.keys(rel);
  return (
    <>
      <Card radius={17} pad={14} style={{ marginBottom: 9 }}>
        <Row gap={12}>
          <GlyphDot glyph="As" size={34} fontSize={12} bg={th.soft(0.15)} color={th.c.accent} />
          <View style={{ flex: 1 }}>
            <T weight={600} style={{ fontSize: 14.5 }}>{t('avakhada.lagna')}</T>
            <T v="mono" style={{ fontSize: 10.5, marginTop: 2 }}>{tr('sign', l.sign)} {l.degree_dms} · {tr('nakshatra', l.nakshatra.name)} {l.nakshatra.pada}</T>
          </View>
        </Row>
      </Card>
      {chart.planets.map((p) => {
        const isOpen = open === p.code;
        const tone = GOOD.includes(p.dignity) ? 'good' : BAD.includes(p.dignity) ? 'bad' : undefined;
        return (
          <Pressable key={p.code} onPress={() => setOpen(isOpen ? null : p.code)} style={{
            backgroundColor: th.c.surface, borderRadius: 17, paddingVertical: 14, paddingHorizontal: 15, marginBottom: 9,
            borderWidth: 1, borderColor: isOpen ? th.c.accent : th.c.hair,
          }}>
            <Row gap={12}>
              <GlyphDot glyph={tr('planetShort', p.code)} size={34} fontSize={16} bg={th.soft(0.11)} color={th.c.accent} />
              <View style={{ flex: 1, minWidth: 0 }}>
                <T weight={600} style={{ fontSize: 14.5 }}>{tr('grahaFull', p.code)}</T>
                <T v="mono" style={{ fontSize: 10.5, marginTop: 2 }}>
                  {tr('sign', p.sign)} {p.degree_dms} · {tr('nakshatra', p.nakshatra.name)} {p.nakshatra.pada}
                </T>
              </View>
              <View style={{ alignItems: 'flex-end', gap: 4 }}>
                <Tag tone={tone}>{tr('dignity', p.dignity)}</Tag>
                <Row gap={4}>
                  {p.retrograde && p.code !== 'Ra' && p.code !== 'Ke' ? <Tag tone="neutral">℞ {t('details.retro')}</Tag> : null}
                  {p.combust ? <Tag tone="bad">{t('details.combust')}</Tag> : null}
                </Row>
              </View>
            </Row>
            {isOpen ? (
              <View style={{ marginTop: 10 }}>
                <KV rows={[
                  [t('details.degree'), `${num(p.longitude, 4)}°`],
                  [t('details.house'), `${p.house} · ${t('details.bhava')} ${p.bhava}`],
                  [t('details.nakshatra'), `${tr('nakshatra', p.nakshatra.name)} · ${tr('graha', p.nakshatra.lord)}`],
                  [t('details.navamsa'), tr('sign', p.navamsa_sign)],
                  [t('details.speed'), `${num(p.speed, 4)}°/d`],
                  [t('details.avastha'), `${tr('avastha', p.avastha.baladi)} · ${tr('avastha', p.avastha.jagradadi)}`],
                ]} />
              </View>
            ) : null}
          </Pressable>
        );
      })}
      <T v="section" style={{ marginTop: 14, marginBottom: 10, marginHorizontal: 2 }}>{t('details.relationships')}</T>
      <Card pad={10}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View>
            <Row gap={0}>
              <View style={{ width: 38 }} />
              {codes.map((c) => <Text key={c} style={{ width: 72, textAlign: 'center', color: th.c.accent, fontSize: 14 }}>{tr('planetShort', c)}</Text>)}
            </Row>
            {codes.map((a) => (
              <Row key={a} gap={0} style={{ borderTopWidth: 1, borderTopColor: th.c.hair, paddingVertical: 7 }}>
                <Text style={{ width: 38, color: th.c.accent, fontSize: 14, textAlign: 'center' }}>{tr('planetShort', a)}</Text>
                {codes.map((b) => (
                  <T key={b} v="tiny" style={{ width: 72, textAlign: 'center', color: th.c.ink2 }}>{a === b ? '—' : tr('dignity', rel[a][b])}</T>
                ))}
              </Row>
            ))}
          </View>
        </ScrollView>
      </Card>
    </>
  );
}

function BirthPanchang({ chart }) {
  const { t, tr, lang } = useI18n();
  const p = chart.panchang;
  const b = chart.dasha_balance;
  const two = (a, s) => <View><T style={{ fontSize: 13.5 }}>{a}</T><T v="mono" style={{ fontSize: 10.5, marginTop: 2 }}>{s}</T></View>;
  return (
    <Card pad={16}>
      <KV rows={[
        [t('panchang.tithi'), two(`${tr('paksha', p.tithi.paksha)} ${tr('tithi', p.tithi.name)}`, range(p.tithi.start, p.tithi.end, lang))],
        [t('panchang.vara'), `${tr('weekday', p.vara.name)} · ${tr('graha', p.vara.lord)}`],
        [t('panchang.nakshatra'), two(`${tr('nakshatra', p.nakshatra.name)} · ${t('panchang.pada', { n: p.nakshatra.pada })}`, range(p.nakshatra.start, p.nakshatra.end, lang))],
        [t('panchang.yoga'), two(tr('yoga', p.yoga.name), range(p.yoga.start, p.yoga.end, lang))],
        [t('panchang.karana'), two(tr('karana', p.karana.name), range(p.karana.start, p.karana.end, lang))],
        [t('details.month'), `${p.lunar_month.is_adhika ? `${t('panchang.adhika')} ` : ''}${tr('month', p.lunar_month.amanta)}`],
        [`${t('details.sunrise')} / ${t('details.sunset')}`, `${clock(p.sunrise, lang, true)} / ${clock(p.sunset, lang, true)}`],
        [t('details.birth'), p.is_day_birth ? t('details.day') : t('details.night')],
        [t('details.ayanamsa'), chart.meta.ayanamsa.dms],
        [t('details.dashaBalance'), `${tr('graha', b.lord)} · ${t('details.ymd', { y: b.years, m: b.months, d: Math.round(b.days) })}`],
      ]} />
    </Card>
  );
}

const AVAKHADA_TERM = { lagna: 'sign', rashi: 'sign', lagna_lord: 'graha', rashi_lord: 'graha', nakshatra_lord: 'graha', nakshatra: 'nakshatra' };

function Avakhada({ chart }) {
  const { t, tr } = useI18n();
  return (
    <Card pad={16}>
      <KV rows={Object.entries(chart.avakhada).map(([k, v]) => [
        t(`avakhada.${k}`), typeof v === 'number' ? String(v) : tr(AVAKHADA_TERM[k] || 'avakhada', v),
      ])} />
    </Card>
  );
}
