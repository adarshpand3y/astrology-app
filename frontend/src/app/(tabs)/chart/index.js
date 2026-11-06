import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';

import { NorthChart, planetMarks, SouthChart } from '../../../components/charts/Charts';
import { Icon, ProIcon } from '../../../components/Icons';
import { Button, Card, Empty, ErrorView, GlyphDot, Loading, Pill, Row, Screen, Seg, Sheet, T } from '../../../components/ui';
import { brand } from '../../../config/env';
import { useAccount, useBilling, useChart, useDashaCurrent, useStrength, useVarga } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { PLANET_CODES } from '../../../i18n/terms';
import { usePrefs } from '../../../state/PrefsContext';
import { useTheme } from '../../../theme';

const SIGN_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];
// Lord of each sign, Aries..Pisces.
const SIGN_LORD = ['Ma', 'Ve', 'Me', 'Mo', 'Su', 'Me', 'Ve', 'Ma', 'Ju', 'Sa', 'Sa', 'Ju'];
const MORE = ['D2', 'D3', 'D4', 'D7', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'];

function EntryCard({ icon, title, sub, onPress }) {
  const th = useTheme();
  return (
    <Card radius={17} pad={14} onPress={onPress} style={{ flexDirection: 'row', alignItems: 'center', gap: 13, marginTop: 12, paddingHorizontal: 15 }}>
      <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
        <Icon name={icon} size={21} color={th.c.accent} />
      </View>
      <View style={{ flex: 1 }}>
        <T v="cardTitle">{title}</T>
        <T v="caption" style={{ marginTop: 1 }}>{sub}</T>
      </View>
      <Text style={{ color: th.c.ink3, fontSize: 16 }}>›</Text>
    </Card>
  );
}

/** Edge fade over the division strip, from the page background to clear. */
function EdgeFade({ side }) {
  const th = useTheme();
  const id = `fade-${side}`;
  return (
    <View pointerEvents="none" style={{ position: 'absolute', top: 0, bottom: 0, width: 44, [side]: 0 }}>
      <Svg width="100%" height="100%">
        <Defs>
          <LinearGradient id={id} x1={side === 'right' ? '1' : '0'} y1="0" x2={side === 'right' ? '0' : '1'} y2="0">
            <Stop offset="0.35" stopColor={th.c.bg} stopOpacity="1" />
            <Stop offset="1" stopColor={th.c.bg} stopOpacity="0" />
          </LinearGradient>
        </Defs>
        <Rect width="100%" height="100%" fill={`url(#${id})`} />
      </Svg>
    </View>
  );
}

/**
 * D2–D60 in a horizontal strip, labelled with how many there are and a swipe cue. Fades and a
 * round arrow at an edge show there is more that way; the arrow also pages the strip.
 */
function DivisionStrip({ varga, isPro, onPick }) {
  const th = useTheme();
  const { t } = useI18n();
  const ref = useRef(null);
  const [m, setM] = useState({ x: 0, width: 0, content: 0 });
  const more = m.content > m.width + 1;
  const atStart = m.x <= 2;
  const atEnd = m.x + m.width >= m.content - 2;
  const page = (dir) => ref.current?.scrollTo({ x: Math.max(0, m.x + dir * m.width * 0.75), animated: true });
  const arrow = (dir) => (
    <Pressable onPress={() => page(dir)} hitSlop={8} accessibilityRole="button"
      accessibilityLabel={t(dir > 0 ? 'chart.moreNext' : 'chart.morePrev')}
      style={{
        position: 'absolute', top: '50%', marginTop: -14, [dir > 0 ? 'right' : 'left']: 0, width: 28, height: 28,
        borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: th.c.surface,
        borderWidth: 1, borderColor: th.c.hair2,
      }}>
      <Text style={[th.font.ui(700), { fontSize: 14, lineHeight: 16, color: th.c.accent }]}>{dir > 0 ? '›' : '‹'}</Text>
    </Pressable>
  );
  return (
    <View style={{ marginBottom: 16 }}>
      <Row style={{ justifyContent: 'space-between', marginBottom: 7, marginHorizontal: 2 }}>
        <T v="eyebrow" style={{ fontSize: 9.5 }}>{t('chart.moreCount', { n: MORE.length })}</T>
        {more ? (
          <T v="tiny" weight={600} style={{ fontSize: 10.5, color: th.c.accent }}>
            {atEnd ? t('chart.swipeBack') : t('chart.swipeMore')}
          </T>
        ) : null}
      </Row>
      <View>
        <ScrollView ref={ref} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 7, paddingRight: 30 }}
          scrollEventThrottle={32}
          onScroll={(e) => { const x = e.nativeEvent.contentOffset.x; setM((s) => (Math.abs(s.x - x) > 1 ? { ...s, x } : s)); }}
          onLayout={(e) => { const width = e.nativeEvent.layout.width; setM((s) => ({ ...s, width })); }}
          onContentSizeChange={(content) => setM((s) => ({ ...s, content }))}>
          {MORE.map((code) => (
            <Pill key={code} surface onPress={() => onPick(code)}
              style={varga === code ? { borderColor: th.c.accent, backgroundColor: th.soft(0.08) } : null}>
              <T v="tiny" weight={600} style={{ color: varga === code ? th.c.accentDark : th.c.ink2 }}>{code}{isPro ? null : <>{' '}<ProIcon size={10} /></>}</T>
            </Pill>
          ))}
        </ScrollView>
        {more && !atStart ? <><EdgeFade side="left" />{arrow(-1)}</> : null}
        {more && !atEnd ? <><EdgeFade side="right" />{arrow(1)}</> : null}
      </View>
    </View>
  );
}

export default function Kundali() {
  const th = useTheme();
  const { t, tr } = useI18n();
  const router = useRouter();
  const { prefs } = usePrefs();
  const { profileId } = useAccount();
  const chart = useChart(profileId);
  const strength = useStrength(profileId);
  const current = useDashaCurrent(profileId);
  const billing = useBilling();
  const [style, setStyle] = useState(null);
  const [varga, setVarga] = useState('D1');
  const [house, setHouse] = useState(null);
  // A chart cached before upgrading to Pro holds only D1: fetch the picked division on its own.
  const extra = useVarga(profileId, varga, varga === 'D1' || !chart.data || !!chart.data.vargas[varga]);

  if (!profileId) {
    return <Screen><Empty title={t('home.noProfileTitle')} sub={t('home.noProfileSub')}
      action={<Button title={t('profiles.add')} onPress={() => router.push('/profile/new')} />} /></Screen>;
  }
  if (chart.loading) return <Screen><Loading /></Screen>;
  if (!chart.data) return <Screen><ErrorView error={chart.error} onRetry={chart.refetch} /></Screen>;

  const data = chart.data;
  const isPro = !!billing.data?.is_pro;
  const chartStyle = brand.features.southIndianChart ? style || prefs.chartStyle : 'north';
  const v = data.vargas[varga] || extra.data || data.vargas.D1;
  const vargaPending = varga !== 'D1' && !data.vargas[varga] && !extra.data;
  const pickVarga = (code) => {
    if (code !== 'D1' && !isPro && !data.vargas[code]) { router.push('/paywall'); return; }
    setVarga(code);
  };

  const titleFor = () => (v.code === 'D1' ? t('chart.d1Title') : v.code === 'D9' ? t('chart.d9Title')
    : t('chart.otherTitle', { code: v.code, name: tr('varga', v.name) }));
  const subFor = () => (v.code === 'D1' ? t('chart.d1Sub') : v.code === 'D9' ? t('chart.d9Sub') : t('chart.otherSub'));

  // Degrees within the sign, for the birth chart (D1) only — divisional charts have no degrees.
  const degrees = v.code === 'D1' && data.lagna ? {
    ...Object.fromEntries(data.planets.map((p) => [p.code, p.degree])), Asc: data.lagna.degree,
  } : undefined;
  const asc = v.ascendant.sign_index;
  const houseSign = house ? ((asc + house - 2) % 12) + 1 : null;
  const occupants = house ? v.planets.filter((p) => p.house === house) : [];
  const lord = houseSign ? v.planets.find((p) => p.code === SIGN_LORD[houseSign - 1]) : null;
  const markWords = (p) => [
    p.retrograde && t('chart.markRetro'), p.combust && t('chart.markCombust'),
    p.dignity === 'exalted' && t('chart.markExalted'), p.dignity === 'debilitated' && t('chart.markDebilitated'),
  ].filter(Boolean).join(' · ');
  const s = strength.data?.summary;
  const chain = current.data?.periods?.slice(0, 2).map((p) => tr('graha', p.lord)).join(' › ');

  return (
    <Screen refreshing={chart.refreshing} onRefresh={chart.refetch}>
      <Row align="baseline" style={{ justifyContent: 'space-between', paddingHorizontal: 2, paddingTop: 8, paddingBottom: 3 }}>
        <T v="screenTitle">{t('chart.title')}</T>
        <T v="mono" style={{ fontSize: 10.5, letterSpacing: 1 }}>{titleFor()}</T>
      </Row>
      <T v="small" style={{ fontSize: 12, paddingHorizontal: 2, paddingBottom: 14 }}>{subFor()}</T>

      {brand.features.southIndianChart ? (
        <Seg options={[{ value: 'north', label: t('chart.north') }, { value: 'south', label: t('chart.south') }]}
          value={chartStyle} onChange={setStyle} style={{ marginBottom: 10 }} />
      ) : null}
      <Seg options={[{ value: 'D1', label: t('chart.d1') }, { value: 'D9', label: t('chart.d9') }]}
        value={['D1', 'D9'].includes(varga) ? varga : null} onChange={pickVarga}
        lockedValues={isPro ? [] : ['D9']} style={{ marginBottom: brand.features.moreDivisions ? 10 : 18 }} />
      {brand.features.moreDivisions ? <DivisionStrip varga={varga} isPro={isPro} onPick={pickVarga} /> : null}

      <Card pad={18} shadow>
        {vargaPending ? (
          <View style={{ aspectRatio: 1, justifyContent: 'center' }}>
            {extra.error ? <ErrorView error={extra.error} onRetry={extra.refetch} /> : <Loading />}
          </View>
        ) : chartStyle === 'north'
          ? <NorthChart varga={v} selected={house} onSelect={setHouse} degrees={degrees} />
          : <SouthChart varga={v} selected={house} onSelect={setHouse} centerLabel={v.code} degrees={degrees}
              centerSub={v.code === 'D1' ? tr('varga', 'Rasi') : tr('varga', v.name)} />}
        <T v="tiny" style={{ textAlign: 'center', marginTop: 12 }}>{t('chart.marksKey')}</T>
        <T v="tiny" style={{ textAlign: 'center', marginTop: 4 }}>{t('chart.tapHint')}</T>
      </Card>

      <Row gap={7} style={{ flexWrap: 'wrap', marginTop: 16 }}>
        {PLANET_CODES.map((c) => (
          <Pill key={c} surface style={{ paddingVertical: 6, paddingHorizontal: 10, gap: 6 }}>
            <Text style={{ color: th.c.accent, fontSize: 13 }}>{tr('planetShort', c)}</Text>
            <T v="tiny" style={{ color: th.c.ink2 }}>{tr('graha', c)}</T>
          </Pill>
        ))}
      </Row>

      <EntryCard icon="timeline-clock-outline" title={t('chart.dashaTitle')} sub={chain ? t('chart.dashaSub', { chain }) : '…'}
        onPress={() => router.push('/chart/dasha')} />
      <EntryCard icon="arm-flex" title={t('chart.strengthTitle')}
        sub={s ? (s.weak_planets || s.weak_houses ? t('chart.strengthSub', { p: s.weak_planets, h: s.weak_houses }) : t('chart.strengthOk')) : '…'}
        onPress={() => router.push('/chart/strength')} />
      {brand.features.birthDetails ? (
        <EntryCard icon="card-account-details-outline" title={t('chart.detailsTitle')} sub={t('chart.detailsSub')} onPress={() => router.push('/chart/details')} />
      ) : null}

      <Sheet visible={!!house} onClose={() => setHouse(null)}>
        {house ? (
          <>
            <Row gap={13} style={{ marginBottom: 14 }}>
              <View style={{ width: 46, height: 46, borderRadius: 14, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
                <Text style={[th.font.display(500), { fontSize: 20, color: th.c.accent }]}>{house}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <T weight={600} style={{ fontSize: 17 }}>{t('chart.houseTitle', { karaka: t('chart.karakas')[house - 1], n: house })}</T>
                <T v="small">{tr('sign', SIGN_EN[houseSign - 1])} · {t('chart.meanings')[house - 1]}</T>
              </View>
            </Row>
            {lord ? (
              <>
                <T v="eyebrow" style={{ marginBottom: 8 }}>{t('chart.lord')}</T>
                {/* Tapping the lord jumps to the house it sits in. */}
                <Pressable onPress={() => lord.house !== house && setHouse(lord.house)}
                  style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 11, marginBottom: 14,
                    borderBottomWidth: 1, borderBottomColor: th.c.hair }}>
                  <GlyphDot glyph={tr('planetShort', lord.code)} size={30} bg={th.soft(0.1)} color={th.c.accent} />
                  <View style={{ flex: 1 }}>
                    <T style={{ fontSize: 14 }}>{tr('grahaFull', lord.code)}{planetMarks(lord) ? `  ${planetMarks(lord)}` : ''}</T>
                    <T v="caption" style={{ marginTop: 2 }}>
                      {lord.house === house ? t('chart.lordHere', { sign: tr('sign', lord.sign) })
                        : t('chart.lordIn', { h: lord.house, karaka: t('chart.karakas')[lord.house - 1], sign: tr('sign', lord.sign) })}
                    </T>
                  </View>
                  {lord.house !== house ? <Text style={{ color: th.c.ink3, fontSize: 16 }}>›</Text> : null}
                </Pressable>
              </>
            ) : null}
            <T v="eyebrow" style={{ marginBottom: 8 }}>{t('chart.placements')}</T>
            {(occupants.length ? occupants : [null]).map((p, i) => (
              <Pressable key={p?.code || i} onPress={() => { if (p) { setHouse(null); router.push('/chart/details'); } }}
                style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 11, borderBottomWidth: 1, borderBottomColor: th.c.hair }}>
                <GlyphDot glyph={p ? tr('planetShort', p.code) : '·'} size={30} bg={th.soft(0.1)} color={th.c.accent} fontSize={15} />
                <View style={{ flex: 1 }}>
                  <T style={{ fontSize: 14 }}>{p ? tr('grahaFull', p.code) : t('chart.emptyHouse')}</T>
                  {p && planetMarks(p) ? <T v="caption" style={{ marginTop: 2 }}>{markWords(p)}</T> : null}
                </View>
              </Pressable>
            ))}
          </>
        ) : null}
      </Sheet>
    </Screen>
  );
}
