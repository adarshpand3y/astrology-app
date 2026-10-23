import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';

import { remediesApi } from '../../../api/endpoints';
import {
  BackLink, Bar, Bullet, Button, Card, ErrorView, GlyphDot, Loading, PanelHeading, Row, Screen, Seg, SoftPanel, T,
} from '../../../components/ui';
import { brand } from '../../../config/env';
import { invalidate } from '../../../hooks/useApi';
import { useAccount, useStrength } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { num } from '../../../utils/format';

const MARKER = 1 / 1.6; // ratio 1.0 on a 0–1.6 scale = 62.5%

export default function Strength() {
  const { t } = useI18n();
  const params = useLocalSearchParams();
  const { profileId } = useAccount();
  const { data, error, loading, refreshing, refetch } = useStrength(profileId);
  const [tab, setTab] = useState(params.tab === 'bhava' ? 'bhava' : 'shad');
  const [planet, setPlanet] = useState(params.planet || null);
  const [house, setHouse] = useState(7);

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <BackLink label={t('strength.back')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 3 }}>{t('strength.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 16 }}>{t('strength.sub')}</T>
      <Seg options={[{ value: 'shad', label: t('strength.shad') }, { value: 'bhava', label: t('strength.bhava') }]}
        value={tab} onChange={setTab} style={{ marginBottom: 18 }} />
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data && tab === 'shad' ? <Shadbala data={data} open={planet} setOpen={setPlanet} /> : null}
      {data && tab === 'bhava' ? (
        <Bhavabala data={data} selected={house} setSelected={setHouse}
          onLord={(code) => { setTab('shad'); setPlanet(code); }} />
      ) : null}
    </Screen>
  );
}

function Shadbala({ data, open, setOpen }) {
  const th = useTheme();
  const { t, tr } = useI18n();
  const router = useRouter();
  const s = data.summary;

  const addRemedy = async (code) => {
    try {
      await remediesApi.add(code);
      invalidate('remedies:');
      Alert.alert(t('strength.added'));
      router.push('/remedies');
    } catch (e) {
      if (e.code === 'pro_required') router.push('/paywall');
      else Alert.alert(t('common.unknownError'), e.message);
    }
  };

  return (
    <>
      <Card pad={18} shadow style={{ paddingVertical: 16, marginBottom: 14 }}>
        <Row gap={8} align="baseline">
          <Text style={[th.font.display(500), { fontSize: 30, color: th.c.ink, lineHeight: 34 }]}>
            {s.full_strength}<Text style={{ fontSize: 16, color: th.c.ink3 }}> / {s.total}</Text>
          </Text>
          <T v="small" style={{ fontSize: 13 }}>{t('strength.fullStrength')}</T>
        </Row>
        <Row gap={8} style={{ flexWrap: 'wrap', marginTop: 13 }}>
          <View style={{ paddingVertical: 6, paddingHorizontal: 10, borderRadius: 20, backgroundColor: th.kind.good.tint }}>
            <Text style={[th.font.ui(600), { fontSize: 11.5, color: th.kind.good.text }]}>
              {t('strength.strongest', { name: tr('graha', s.strongest.code), r: num(s.strongest.ratio) })}
            </Text>
          </View>
          <View style={{ paddingVertical: 6, paddingHorizontal: 10, borderRadius: 20, backgroundColor: th.kind.bad.tint }}>
            <Text style={[th.font.ui(600), { fontSize: 11.5, color: th.kind.bad.text }]}>
              {t('strength.weakest', { name: tr('graha', s.weakest.code), r: num(s.weakest.ratio) })}
            </Text>
          </View>
        </Row>
        {s.dasha_note ? <T v="small" style={{ fontSize: 12, marginTop: 12, lineHeight: 18.5 }}>{s.dasha_note}</T> : null}
      </Card>
      <Row gap={7} style={{ paddingHorizontal: 2, paddingBottom: 10 }}>
        <View style={{ width: 2, height: 12, backgroundColor: th.c.inv, opacity: 0.55 }} />
        <T v="tiny" style={{ flex: 1 }}>{t('strength.minHint')}</T>
      </Row>

      {data.planets.map((p) => {
        const k = th.kind[p.kind];
        const isOpen = open === p.code;
        const max = Math.max(...p.sources.map((x) => x.virupas), 1);
        return (
          <View key={p.code} style={{
            backgroundColor: th.c.surface, borderRadius: 17, paddingVertical: 14, paddingHorizontal: 15, marginBottom: 9,
            borderWidth: 1, borderColor: isOpen ? th.c.accent : th.c.hair,
          }}>
            <Pressable onPress={() => setOpen(isOpen ? null : p.code)}>
              <Row gap={12}>
                <GlyphDot glyph={tr('planetShort', p.code)} size={34} fontSize={16} bg={k.tint} color={k.solid} />
                <View style={{ flex: 1, minWidth: 0 }}>
                  <T weight={600} style={{ fontSize: 14.5 }}>
                    {tr('grahaFull', p.code)}{p.is_dasha_lord ? <Text style={{ color: th.c.accent, fontSize: 11 }}>  · {t('strength.dashaLord')}</Text> : null}
                  </T>
                  <T v="mono" style={{ fontSize: 10.5, marginTop: 2 }}>{t('strength.rupasNeeds', { v: num(p.total_rupas, 1), r: num(p.required_rupas, 1) })}</T>
                </View>
                <View style={{ alignItems: 'flex-end' }}>
                  <Text style={[th.font.ui(700), { fontSize: 15, color: k.solid }]}>{num(p.ratio)}×</Text>
                  <Text style={[th.font.ui(600), { fontSize: 10, color: k.solid }]}>{p.status}</Text>
                </View>
              </Row>
              <View style={{ height: 6, borderRadius: 4, backgroundColor: th.c.track, marginTop: 11 }}>
                <View style={{ position: 'absolute', left: 0, top: 0, bottom: 0, borderRadius: 4, width: `${Math.min(p.ratio / 1.6, 1) * 100}%`, backgroundColor: k.solid }} />
                <View style={{ position: 'absolute', left: `${MARKER * 100}%`, top: -3, bottom: -3, width: 2, backgroundColor: th.c.inv, opacity: 0.55 }} />
              </View>
            </Pressable>
            {isOpen ? (
              <View>
                <T v="eyebrow" style={{ fontSize: 9, marginTop: 16, marginBottom: 8 }}>{t('strength.sixSources')}</T>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', rowGap: 9, columnGap: 16 }}>
                  {p.sources.map((c) => (
                    <View key={c.key} style={{ width: '46%', flexGrow: 1 }}>
                      <Row style={{ justifyContent: 'space-between' }} align="baseline">
                        <T weight={600} style={{ fontSize: 12 }} numberOfLines={1}>
                          {c.name} <Text style={[th.font.ui(400), { fontSize: 10.5, color: th.c.ink3 }]}>{c.gloss}</Text>
                        </T>
                        <T v="mono" style={{ fontSize: 10.5, color: th.c.ink2 }}>{Math.round(c.virupas)}</T>
                      </Row>
                      <Bar value={c.virupas / max} height={3} color={th.c.accent} style={{ marginTop: 4, opacity: 0.85 }} />
                    </View>
                  ))}
                </View>
                <SoftPanel n={0.1} style={{ borderRadius: 14, marginTop: 16, paddingVertical: 13 }}>
                  <PanelHeading>{t('strength.whatToDo')}</PanelHeading>
                  <T v="small" style={{ marginBottom: 6, color: th.c.ink2 }}>{p.advice.head}</T>
                  {p.advice.items.map((a) => <Bullet key={a.title} title={a.title} detail={a.detail} />)}
                  {p.kind === 'bad' && brand.features.remedies ? (
                    <Button small title={t('strength.addRemedy')} onPress={() => addRemedy(p.code)} style={{ marginTop: 8 }} />
                  ) : null}
                </SoftPanel>
              </View>
            ) : null}
          </View>
        );
      })}
    </>
  );
}

function Bhavabala({ data, selected, setSelected, onLord }) {
  const th = useTheme();
  const { t, tr } = useI18n();
  const houses = data.houses;
  const min = data.summary.house_minimum;
  const scale = Math.max(10, ...houses.map((h) => h.rupas)) * 1.05;
  const H = 130;
  const h = houses.find((x) => x.house === selected) || houses[0];
  const k = th.kind[h.kind];
  const lord = data.planets.find((p) => p.code === h.lord);
  const SIGN_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

  return (
    <>
      <Card pad={14} shadow style={{ paddingVertical: 16, paddingBottom: 12 }}>
        <Row align="baseline" style={{ justifyContent: 'space-between', paddingHorizontal: 4, paddingBottom: 12 }}>
          <T weight={600} style={{ fontSize: 14 }}>{t('strength.houseStrength')}</T>
          <T v="mono" style={{ fontSize: 10 }}>{t('strength.rupasMin', { m: num(min, 1) })}</T>
        </Row>
        <View style={{ height: H, flexDirection: 'row', alignItems: 'flex-end', gap: 5 }}>
          <View style={{ position: 'absolute', left: 0, right: 0, bottom: (min / scale) * H, borderTopWidth: 1.5, borderStyle: 'dashed', borderColor: th.c.hair2 }} />
          {houses.map((x) => {
            const sel = x.house === selected;
            const c = th.kind[x.kind].solid;
            return (
              <Pressable key={x.house} onPress={() => setSelected(x.house)} style={{ flex: 1, height: '100%', justifyContent: 'flex-end', alignItems: 'center', gap: 4 }}>
                <Text style={[th.font.ui(700), { fontSize: 9.5, color: c, opacity: sel ? 1 : 0 }]}>{num(x.rupas, 1)}</Text>
                <View style={{
                  width: '100%', height: Math.max(4, (x.rupas / scale) * H - 14), borderTopLeftRadius: 5, borderTopRightRadius: 5,
                  borderBottomLeftRadius: 2, borderBottomRightRadius: 2, backgroundColor: c, opacity: sel ? 1 : 0.45,
                  borderWidth: sel ? 2 : 0, borderColor: th.c.accent,
                }} />
              </Pressable>
            );
          })}
        </View>
        <Row gap={5} style={{ marginTop: 6 }}>
          {houses.map((x) => (
            <Text key={x.house} style={[th.font.mono(x.house === selected ? 600 : 400), {
              flex: 1, textAlign: 'center', fontSize: 10, color: x.house === selected ? th.c.accent : th.c.ink3,
            }]}>{x.house}</Text>
          ))}
        </Row>
      </Card>

      <Card pad={18} style={{ marginTop: 14, paddingVertical: 16 }}>
        <Row gap={13}>
          <View style={{ width: 46, height: 46, borderRadius: 14, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
            <Text style={[th.font.display(500), { fontSize: 20, color: th.c.accent }]}>{h.house}</Text>
          </View>
          <View style={{ flex: 1, minWidth: 0 }}>
            <T weight={600} style={{ fontSize: 16 }}>{t('chart.houseTitle', { karaka: h.karaka, n: h.house })}</T>
            <T v="small" style={{ fontSize: 12 }}>{tr('sign', SIGN_EN[h.rasi_sign_index - 1])} · {h.meaning}</T>
          </View>
          <View style={{ alignItems: 'flex-end' }}>
            <Text style={[th.font.ui(700), { fontSize: 16, color: k.solid }]}>{num(h.rupas, 1)}</Text>
            <Text style={[th.font.ui(600), { fontSize: 10, color: k.solid }]}>{h.status}</Text>
          </View>
        </Row>
        <Row gap={8} align="stretch" style={{ marginTop: 14 }}>
          {h.components.filter((c) => c.key !== 'other' || Math.abs(c.rupas) > 0.05).map((c) => (
            <View key={c.key} style={{ flex: 1, backgroundColor: th.c.muted, borderRadius: 11, paddingVertical: 9, paddingHorizontal: 10 }}>
              <T v="tiny" style={{ fontSize: 10, lineHeight: 13 }}>{c.name}</T>
              <T v="mono" style={{ fontSize: 13, color: th.c.ink, marginTop: 3, fontWeight: '600' }}>{num(c.rupas, 1)}</T>
            </View>
          ))}
        </Row>
        <Pressable onPress={() => onLord(h.lord)} style={{
          flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12, paddingTop: 10, paddingBottom: 2,
          borderTopWidth: 1, borderTopColor: th.c.hair,
        }}>
          <T v="small" style={{ flex: 1, fontSize: 12 }}>
            {t('strength.houseLord')}<Text style={[th.font.ui(600), { color: th.c.ink }]}>{tr('graha', h.lord)}</Text>
            {lord ? t('strength.lordAt', { r: `${num(lord.ratio)}×` }) : ''}
          </T>
          <T v="link">{t('strength.shadLink')}</T>
        </Pressable>
        <SoftPanel n={0.1} style={{ borderRadius: 14, marginTop: 12, paddingVertical: 13 }}>
          <PanelHeading>{t('strength.whatToDo')}</PanelHeading>
          {h.advice.map((a) => <Bullet key={a}><T v="small" style={{ color: th.c.ink2 }}>{a}</T></Bullet>)}
        </SoftPanel>
      </Card>
    </>
  );
}
