import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, View } from 'react-native';

import { BackLink, Bar, Card, ErrorView, GlyphDot, Loading, ProLock, Row, Screen, T } from '../../../components/ui';
import { useAccount, useBilling, useChart, useDashaCurrent, useDashaLevel } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { dashaDate, displayDate, displayTime, duration, progress } from '../../../utils/format';

const FREE_DEPTH = 1; // free users can open the Antardashas of a Mahadasha (path length 1)

export default function Dasha() {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const router = useRouter();
  const { profileId } = useAccount();
  const billing = useBilling();
  const isPro = !!billing.data?.is_pro;
  const chart = useChart(profileId);
  const current = useDashaCurrent(profileId);
  const [path, setPath] = useState([]);
  const level = useDashaLevel(profileId, path.join('/'));
  const [now] = useState(() => Date.now());
  const levels = t('dasha.levels');
  const levelSubs = t('dasha.levelSubs');

  const go = (next) => {
    if (next.length > FREE_DEPTH && !isPro) { router.push('/paywall'); return; }
    setPath(next);
  };

  const chain = current.data?.periods || [];
  const birth = chart.data?.meta?.birth_utc;
  const kids = level.data?.periods || [];
  const L = path.length;
  const spanA = L ? Date.parse(level.data?.parent?.start) : Date.parse(birth || kids[0]?.start);
  const spanB = L ? Date.parse(level.data?.parent?.end) : Date.parse(kids[kids.length - 1]?.end);
  const status = (p) => (Date.parse(p.end) <= now ? 'past' : Date.parse(p.start) > now ? 'ahead' : 'now');
  const startOf = (p) => (L === 0 && birth && Date.parse(p.start) < Date.parse(birth) ? birth : p.start);
  const drill = L < 4;

  return (
    <Screen refreshing={level.refreshing} onRefresh={() => { level.refetch(); current.refetch(); }}>
      <BackLink label={t('chart.title')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 2 }}>{t('dasha.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 16 }}>{t('dasha.sub')}</T>

      {/* you are in · now */}
      <Card pad={16} shadow style={{ paddingTop: 14, paddingBottom: 6 }}>
        <Row align="baseline" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
          <T v="eyebrow">{t('dasha.now')}</T>
          <T v="mono" style={{ fontSize: 10 }}>{`${displayDate(new Date(), lang)} · ${displayTime(new Date(), lang)}`}</T>
        </Row>
        {current.loading ? <Loading style={{ paddingVertical: 20 }} /> : null}
        {chain.map((p, i) => (
          <Pressable key={p.path} onPress={() => go(chain.slice(0, i).map((x) => x.lord))} style={{
            flexDirection: 'row', alignItems: 'center', gap: 11, paddingVertical: 10, paddingLeft: i * 12,
            borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair,
          }}>
            <GlyphDot glyph={tr('planetShort', p.lord)} size={28} fontSize={13} color="#fff"
              bg={i ? `${th.c.accent}${Math.round((1 - i * 0.14) * 255).toString(16).padStart(2, '0')}` : th.c.accent} />
            <View style={{ flex: 1, minWidth: 0 }}>
              <T weight={600} numberOfLines={1} style={{ fontSize: 14 }}>
                {chain.slice(0, i + 1).map((x) => tr('graha', x.lord)).join(' › ')}
              </T>
              <T v="caption" style={{ fontSize: 11, marginTop: 1 }}>{levels[i]}</T>
            </View>
            <View style={{ alignItems: 'flex-end', gap: 5 }}>
              <T v="mono" style={{ fontSize: 10.5, color: th.c.ink2 }}>{t('dasha.left', { d: duration(Date.parse(p.end) - now, lang) })}</T>
              <Bar value={progress(p.start, p.end, now)} height={3} style={{ width: 54 }} />
            </View>
          </Pressable>
        ))}
      </Card>

      {/* breadcrumbs */}
      <Row gap={6} style={{ flexWrap: 'wrap', marginTop: 20, marginBottom: 12 }}>
        {[{ label: t('dasha.all'), p: [] }, ...path.map((k, i) => ({ label: tr('graha', k), p: path.slice(0, i + 1) }))].map((c, i, a) => {
          const last = i === a.length - 1;
          return (
            <Row key={i} gap={6}>
              {i ? <Text style={{ color: th.c.ink3, fontSize: 11 }}>›</Text> : null}
              <Pressable onPress={() => setPath(c.p)} style={{
                paddingVertical: 5, paddingHorizontal: 10, borderRadius: 20, backgroundColor: last ? th.c.accent : th.soft(0.1),
              }}>
                <Text style={[th.font.ui(600), { fontSize: 12, color: last ? th.c.onAccent : th.c.accentDark }]}>{c.label}</Text>
              </Pressable>
            </Row>
          );
        })}
      </Row>

      {/* level header */}
      <Row align="baseline" style={{ justifyContent: 'space-between', paddingHorizontal: 2 }}>
        <T weight={600} style={{ fontSize: 16 }}>{levels[L]}</T>
        {kids.length ? (
          <T v="mono" style={{ fontSize: 10 }}>
            {dashaDate(new Date(spanA).toISOString(), Math.min(L, 3), lang)} – {dashaDate(new Date(spanB).toISOString(), Math.min(L, 3), lang)}
          </T>
        ) : null}
      </Row>
      <T v="caption" style={{ paddingHorizontal: 2, paddingTop: 2, paddingBottom: 12 }}>
        {L ? t('dasha.within', { sub: levelSubs[L], chain: path.map((k) => tr('graha', k)).join(' › ') }) : t('dasha.sequence', { sub: levelSubs[0] })}
      </T>

      {level.loading ? <Loading /> : null}
      {level.error?.code === 'pro_required' ? <ProLock text={t('dasha.locked')} /> : <ErrorView error={level.error} onRetry={level.refetch} />}

      {kids.length ? (
        <>
          {/* proportional strip */}
          <View style={{ marginBottom: 16 }}>
            <View style={{ flexDirection: 'row', gap: 2, height: 22, borderRadius: 7, overflow: 'hidden' }}>
              {kids.map((p) => {
                const st = status(p);
                const len = Date.parse(p.end) - Date.parse(startOf(p));
                const share = len / (spanB - spanA);
                return (
                  <View key={p.path} style={{
                    flex: Math.max(len, 1), alignItems: 'center', justifyContent: 'center',
                    backgroundColor: st === 'now' ? th.c.accent : st === 'past' ? th.c.hair2 : th.soft(0.14),
                  }}>
                    {share > 0.06 ? <Text style={{ fontSize: 11, color: st === 'now' ? '#fff' : st === 'past' ? th.c.ink3 : th.c.accent }}>{tr('planetShort', p.lord)}</Text> : null}
                  </View>
                );
              })}
            </View>
            {now >= spanA && now < spanB ? (
              <View style={{ position: 'absolute', top: -4, bottom: -4, width: 2, borderRadius: 1, backgroundColor: th.c.inv, left: `${((now - spanA) / (spanB - spanA)) * 100}%` }} />
            ) : null}
          </View>

          {kids.map((p) => {
            const st = status(p);
            const nowRow = st === 'now';
            const start = startOf(p);
            const locked = drill && L + 1 > FREE_DEPTH && !isPro;
            return (
              <Pressable key={p.path} disabled={!drill} onPress={() => go([...path, p.lord])} style={{
                flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 14, borderRadius: 15,
                marginBottom: 8, borderWidth: 1, borderColor: nowRow ? th.c.accent : th.c.hair,
                backgroundColor: nowRow ? th.soft(0.07) : th.c.surface, opacity: st === 'past' ? 0.6 : 1,
              }}>
                <GlyphDot glyph={tr('planetShort', p.lord)} size={32} fontSize={15} bg={nowRow ? th.c.accent : th.soft(0.11)} color={nowRow ? '#fff' : th.c.accent} />
                <View style={{ flex: 1, minWidth: 0 }}>
                  <Row gap={8}>
                    <T weight={600} style={{ fontSize: 14.5 }}>{tr('graha', p.lord)}</T>
                    <Text style={[th.font.ui(600), {
                      fontSize: 11,
                      color: nowRow ? th.c.accent : st === 'past' ? th.c.ink3 : th.kind.good.solid,
                    }]}>{t(`dasha.${st === 'now' ? 'current' : st}`)}</Text>
                  </Row>
                  <T v="mono" style={{ fontSize: 10.5, marginTop: 3 }}>
                    {dashaDate(start, L, lang)} – {dashaDate(p.end, L, lang)}{start !== p.start ? t('dasha.fromBirth') : ''}
                  </T>
                  {nowRow ? <Bar value={progress(p.start, p.end, now)} height={3} style={{ marginTop: 7 }} /> : null}
                </View>
                <Row gap={8}>
                  <T v="mono" style={{ fontSize: 10.5, color: th.c.ink2 }}>{duration(Date.parse(p.end) - Date.parse(start), lang)}</T>
                  {drill ? <Text style={{ color: th.c.ink3, fontSize: 14 }}>{locked ? '◆' : '›'}</Text> : null}
                </Row>
              </Pressable>
            );
          })}
          <T v="tiny" style={{ textAlign: 'center', marginTop: 10 }}>
            {drill ? t('dasha.drillHint', { level: levels[L + 1] }) : t('dasha.deepest')}
          </T>
        </>
      ) : null}
    </Screen>
  );
}
