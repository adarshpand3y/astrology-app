// "Planets right now" on Home: a table of every graha (sign, house, degree, nakshatra) with
// Retro / Combust / Exalted / Debilitated badges and filters. Tapping a graha in one of those
// conditions opens what to do and what to avoid while it lasts.
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { useI18n } from '../i18n';
import { GLYPH } from '../i18n/terms';
import { useTheme } from '../theme';
import { shortDate } from '../utils/format';
import { Card, Row, T } from './ui';

const pad2 = (n) => String(n).padStart(2, '0');
/** 3.4 -> "3°24′" (truncated, never rounds up to the next degree). */
const dms = (deg) => {
  const m = Math.floor(deg * 60);
  return `${Math.floor(m / 60)}°${pad2(m % 60)}′`;
};
const ordinal = (n) => {
  const s = n % 100 >= 11 && n % 100 <= 13 ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th';
  return `${n}${s}`;
};
// Badge / pill tones per condition (the design: retro amber, combust red, exalted green, debilitated grey).
const TONE = { retrograde: 'neutral', combust: 'bad', exalted: 'good', debilitated: null };

function Badge({ label, tone, size = 9.5 }) {
  const th = useTheme();
  const k = tone ? th.kind[tone] : { tint: th.c.muted, text: th.c.ink2 };
  return (
    <View style={{ backgroundColor: k.tint, borderRadius: 20, paddingVertical: 2, paddingHorizontal: 7 }}>
      <Text style={[th.font.ui(700), { fontSize: size, color: k.text }]}>{label}</Text>
    </View>
  );
}

function Guide({ g }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  const list = (items, color) => items.map((x) => (
    <Text key={x} style={[th.font.ui(400), {
      fontSize: 11.5, lineHeight: 16.5, color: th.c.ink, paddingVertical: 3, paddingLeft: 9, marginBottom: 5,
      borderLeftWidth: 2, borderLeftColor: color,
    }]}>{x}</Text>
  ));
  return (
    <View style={{ backgroundColor: th.c.muted, borderRadius: 13, padding: 12 }}>
      <Row gap={7} style={{ flexWrap: 'wrap' }}>
        <Badge label={g.label} tone={TONE[g.condition]} size={10} />
        {g.until ? <T v="tiny" style={{ fontSize: 10.5 }}>{t('home.skyUntil', { d: shortDate(g.until, lang) })}</T> : null}
      </Row>
      <T v="small" style={{ fontSize: 12, lineHeight: 18, marginTop: 7 }}>{g.note}</T>
      <Row gap={10} align="flex-start" style={{ marginTop: 10 }}>
        <View style={{ flex: 1 }}>
          <Text style={[th.font.ui(700), { fontSize: 10, letterSpacing: 0.6, color: th.kind.good.text, marginBottom: 5 }]}>✓ {t('home.skyDo')}</Text>
          {list(g.do, th.kind.good.solid)}
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[th.font.ui(700), { fontSize: 10, letterSpacing: 0.6, color: th.kind.bad.text, marginBottom: 5 }]}>✕ {t('home.skyAvoid')}</Text>
          {list(g.avoid, th.kind.bad.solid)}
        </View>
      </Row>
    </View>
  );
}

export function SkyNow({ sky }) {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const [filter, setFilter] = useState('all');
  const [open, setOpen] = useState(null);
  if (!sky) return null;

  const hi = lang === 'hi';
  const counts = {
    all: sky.planets.length,
    retrograde: sky.planets.filter((p) => p.retrograde).length,
    combust: sky.planets.filter((p) => p.combust).length,
  };
  const rows = filter === 'all' ? sky.planets : sky.planets.filter((p) => p[filter]);
  const ref = sky.reference;

  const pill = (key, label) => {
    const active = filter === key;
    return (
      <Pressable key={key} onPress={() => setFilter(key)} disabled={!counts[key]} style={{
        borderRadius: 20, paddingVertical: 6, paddingHorizontal: 11,
        backgroundColor: active ? th.c.accent : th.c.muted, opacity: counts[key] ? 1 : 0.45,
      }}>
        <Text style={[th.font.ui(600), { fontSize: 11.5, color: active ? th.c.onAccent : th.c.ink2 }]}>{label}</Text>
      </Pressable>
    );
  };

  return (
    <View style={{ marginTop: 22 }}>
      <Row style={{ justifyContent: 'space-between', marginHorizontal: 2, marginBottom: 11 }}>
        <T v="section">{t('home.skyTitle')}</T>
        <Row gap={5} style={{ backgroundColor: th.kind.good.tint, borderRadius: 10, paddingVertical: 3, paddingHorizontal: 8 }}>
          <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: th.kind.good.solid }} />
          <Text style={[th.font.ui(600), { fontSize: 10.5, color: th.kind.good.text }]}>{t('home.liveTransit')}</Text>
        </Row>
      </Row>

      <Card radius={20} pad={0} shadow="card" style={{ overflow: 'hidden' }}>
        <Row gap={6} style={{ flexWrap: 'wrap', paddingVertical: 11, paddingHorizontal: 14, borderBottomWidth: 1, borderBottomColor: th.c.hair }}>
          {pill('all', t('home.skyAll', { n: counts.all }))}
          {pill('retrograde', t('home.skyRetroFilter', { n: counts.retrograde }))}
          {pill('combust', t('home.skyCombustFilter', { n: counts.combust }))}
        </Row>

        {rows.map((p, i) => {
          const tone = p.combust ? 'bad' : p.retrograde ? 'neutral' : 'good';
          const has = p.guide.length > 0;
          const isOpen = has && open === p.planet;
          const signLine = hi ? tr('sign', p.sign) : `${p.sign_sanskrit} · ${p.sign}`;
          const house = t('home.skyHouse', { n: hi ? p.house : ordinal(p.house) });
          return (
            <View key={p.planet} style={{
              borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair, backgroundColor: isOpen ? th.soft(0.04) : 'transparent',
            }}>
              <Pressable disabled={!has} onPress={() => setOpen(isOpen ? null : p.planet)}
                style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 14 }}>
                <View style={{
                  width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: th.kind[tone].tint,
                }}>
                  <Text style={{ fontSize: 15, color: th.kind[tone].solid }}>{GLYPH[p.planet]}</Text>
                </View>
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Row gap={6} style={{ flexWrap: 'wrap' }}>
                    <T weight={600} style={{ fontSize: 14 }}>
                      {hi ? tr('graha', p.planet) : `${tr('graha', p.planet)} · ${tr('planet', p.planet)}`}
                    </T>
                    {p.retrograde ? <Badge tone="neutral" label={t('home.skyRetro')} /> : null}
                    {p.combust ? <Badge tone="bad" label={t('home.skyCombust')} /> : null}
                    {p.dignity === 'exalted' ? <Badge tone="good" label={t('home.skyExalted')} /> : null}
                    {p.dignity === 'debilitated' ? <Badge tone={null} label={t('home.skyDebilitated')} /> : null}
                  </Row>
                  <Text style={[th.font.ui(400), { fontSize: 11.5, color: th.c.ink2, marginTop: 2 }]}>
                    {signLine} <Text style={{ color: th.c.ink3 }}>· {house}</Text>
                  </Text>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <T v="mono" weight={600} style={{ fontSize: 13, color: th.c.ink }}>{dms(p.degree)}</T>
                  <T v="tiny" style={{ fontSize: 10, marginTop: 1 }}>{tr('nakshatra', p.nakshatra)} · {t('home.skyPada', { n: p.pada })}</T>
                </View>
                <Text style={{
                  width: 16, textAlign: 'center', fontSize: 15, color: th.c.ink2, transform: [{ rotate: isOpen ? '180deg' : '0deg' }],
                }}>{has ? '▾' : ''}</Text>
              </Pressable>
              {isOpen ? (
                <View style={{ paddingLeft: 58, paddingRight: 14, paddingBottom: 14, gap: 10 }}>
                  {p.guide.map((g) => <Guide key={g.condition} g={g} />)}
                </View>
              ) : null}
            </View>
          );
        })}

        <View style={{ borderTopWidth: 1, borderTopColor: th.c.hair, paddingVertical: 10, paddingHorizontal: 14 }}>
          <T v="tiny" style={{ fontSize: 10.5, lineHeight: 15 }}>
            {t(ref.basis === 'lagna' ? 'home.skyFootLagna' : 'home.skyFootMoon', {
              sign: tr('sign', ref.sign), ayanamsa: ref.ayanamsa.charAt(0).toUpperCase() + ref.ayanamsa.slice(1),
            })}
          </T>
        </View>
      </Card>
    </View>
  );
}
