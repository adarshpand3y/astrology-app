import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Animated, Pressable, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';

import { LocationPicker } from '../../components/LocationPicker';
import {
  Avatar, Bar, Button, Card, Empty, ErrorView, GradientBadge, Loading, Pill, Row, Screen, Sheet, SoftPanel, T, WindowRow,
} from '../../components/ui';
import { useAccount, useHome } from '../../hooks/data';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { useTheme } from '../../theme';
import { clock, dateLine, duration, initials, range } from '../../utils/format';

export default function Home() {
  const { profileId } = useAccount();
  const { t } = useI18n();
  const router = useRouter();
  if (!profileId) {
    return (
      <Screen>
        <Empty title={t('home.noProfileTitle')} sub={t('home.noProfileSub')}
          action={<Button title={t('profiles.add')} onPress={() => router.push('/profile/new')} />} />
      </Screen>
    );
  }
  return <HomeContent />;
}

function HomeContent() {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const router = useRouter();
  const { user, updateMe } = useAuth();
  const { data, error, loading, refreshing, refetch } = useHome();
  const [whyOpen, setWhyOpen] = useState(true);
  const [placeOpen, setPlaceOpen] = useState(false);

  if (loading) return <Screen><Loading /></Screen>;
  if (!data) return <Screen><ErrorView error={error} onRetry={refetch} /></Screen>;

  const md = data.period.mahadasha;
  const ad = data.period.antardasha;
  const tr8 = data.transit;
  const kind = th.kind[tr8.kind];

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      {/* header */}
      <Row align="flex-start" style={{ justifyContent: 'space-between', paddingHorizontal: 2, paddingTop: 8, paddingBottom: 14 }}>
        <View style={{ flex: 1 }}>
          <Row gap={7} style={{ flexWrap: 'wrap' }}>
            <T v="eyebrow" style={{ fontSize: 10.5, letterSpacing: 1.4 }}>{dateLine(data.date, lang)}</T>
            <Pressable onPress={() => setPlaceOpen(true)} hitSlop={8}>
              <Row gap={4}>
                <Svg width={10} height={10} viewBox="0 0 16 16" fill="none">
                  <Path d="M8 1.5c2.8 0 5 2.2 5 5 0 3.5-5 8-5 8s-5-4.5-5-8c0-2.8 2.2-5 5-5z" stroke={th.c.accent} strokeWidth={1.8} />
                </Svg>
                <T v="eyebrow" style={{ fontSize: 10.5, letterSpacing: 1.4, color: th.c.accent }}>
                  {data.location.city}{data.location.region ? `, ${data.location.region}` : ''}
                </T>
              </Row>
            </Pressable>
          </Row>
          <T v="greeting" style={{ marginTop: 3 }}>{t(`home.${data.greeting}`)}, {data.name}</T>
        </View>
        <Avatar size={40} initials={initials(data.profile.name)} onPress={() => router.push('/profile')} />
      </Row>

      {/* insight */}
      <Card radius={22} pad={20} shadow="hero" style={{ paddingBottom: 18 }}>
        <Row gap={8} style={{ marginBottom: 13 }}>
          <GradientBadge />
          <T v="eyebrow" style={{ fontSize: 10, letterSpacing: 1.3 }}>{t('home.insight')}</T>
        </Row>
        <T v="quote">{data.insight.text}</T>
        <Pressable onPress={() => setWhyOpen((o) => !o)} style={{
          marginTop: 15, borderTopWidth: 1, borderTopColor: th.c.hair, paddingTop: 13,
          flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <Row gap={6}>
            <Text style={{ fontSize: 13, color: th.c.accent }}>◈</Text>
            <T weight={600} style={{ fontSize: 12.5, color: th.c.accent }}>{t('home.why')}</T>
          </Row>
          <Text style={{ fontSize: 11, color: th.c.ink3, transform: [{ rotate: whyOpen ? '180deg' : '0deg' }] }}>▾</Text>
        </Pressable>
        {whyOpen ? (
          <Animated.View>
            <SoftPanel style={{ marginTop: 11, paddingVertical: 13 }}>
              <T v="small" style={{ lineHeight: 20 }}>{data.insight.why}</T>
              <Row gap={7} style={{ flexWrap: 'wrap', marginTop: 11 }}>
                {data.insight.chips.map((c) => <Pill key={c}>{c}</Pill>)}
              </Row>
            </SoftPanel>
          </Animated.View>
        ) : null}
      </Card>

      {/* period + transit */}
      <Row gap={12} align="stretch" style={{ marginTop: 14 }}>
        <Card radius={18} pad={15} style={{ flex: 1 }} onPress={() => router.push('/chart/dasha')}>
          <T v="eyebrow" style={{ fontSize: 9 }}>{t('home.currentPeriod')}</T>
          <T weight={600} numberOfLines={1} style={{ fontSize: 15, marginTop: 8 }}>{tr('graha', md.lord)}–{tr('graha', ad.lord)}</T>
          <T v="tiny" style={{ color: th.c.ink2, marginTop: 6 }}>
            {lang === 'hi' ? t('home.dashaSub', { a: tr('graha', md.lord), b: tr('graha', ad.lord) })
              : t('home.dashaSub', { a: tr('planet', md.lord), b: tr('planet', ad.lord) })}
          </T>
          <Bar value={ad.progress} style={{ marginTop: 9 }} />
          <T v="tiny" style={{ fontSize: 10, marginTop: 5 }}>{t('home.remaining', { d: duration(ad.remaining_seconds * 1000, lang) })}</T>
        </Card>
        <Card radius={18} pad={15} style={{ flex: 1 }} onPress={() => router.push('/chart')}>
          <T v="eyebrow" style={{ fontSize: 9 }}>{t('home.liveTransit')}</T>
          <Row gap={7} style={{ marginTop: 8 }}>
            <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: kind.solid }} />
            <T weight={600} numberOfLines={2} style={{ fontSize: 15, flexShrink: 1 }}>{tr8.title}</T>
          </Row>
          <T v="tiny" style={{ color: th.c.ink2, marginTop: 6 }}>{tr8.gloss}</T>
          {tr8.peak ? (
            <Row gap={5} style={{ marginTop: 11 }}>
              <View style={{ width: 7, height: 7, borderRadius: 4, backgroundColor: kind.solid }} />
              <T v="tiny" style={{ fontSize: 10 }}>{t('home.peaks', { time: clock(tr8.peak, lang, true) })}</T>
            </Row>
          ) : null}
        </Card>
      </Row>

      {/* today's windows */}
      <Row style={{ justifyContent: 'space-between', marginTop: 22, marginBottom: 11, marginHorizontal: 2 }}>
        <T v="section">{t('home.todaysWindows')}</T>
        <Pressable onPress={() => router.push('/timeline')} hitSlop={8}><T v="link">{t('home.fullTimeline')}</T></Pressable>
      </Row>
      {data.windows.map((w) => (
        <WindowRow key={`${w.key}-${w.start}`} name={w.name} gloss={w.short} label={w.kind_label} kind={w.kind}
          time={range(w.start, w.end, lang).replace(/ (AM|PM)$/, '')} />
      ))}

      <Sheet visible={placeOpen} onClose={() => setPlaceOpen(false)}>
        <LocationPicker label={t('auth.livePlace')} hint={t('auth.livePlaceHint')} icon="target" value={user?.current_place}
          onChange={async (p) => { setPlaceOpen(false); await updateMe({ current_place_id: p.id }); }} />
        <View style={{ height: 180 }} />
      </Sheet>
    </Screen>
  );
}
