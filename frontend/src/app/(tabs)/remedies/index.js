import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';

import { remediesApi } from '../../../api/endpoints';
import { Heatmap, MiniHeatmap } from '../../../components/charts/Heatmap';
import { MoodPractice } from '../../../components/charts/MoodPractice';
import { MoodCheckIn } from '../../../components/MoodCheckIn';
import { DoneButton, EditButton, RemedyCard } from '../../../components/RemedyCard';
import { Card, Empty, ErrorView, GradientPanel, Loading, Row, Screen, Seg, T } from '../../../components/ui';
import { brand } from '../../../config/env';
import { invalidate, updateCached } from '../../../hooks/useApi';
import { useAccount, useRemedies, useRemedyHistory } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useTheme } from '../../../theme';
import { DAY_LETTERS, todayISO } from '../../../utils/format';

function Stat({ value, label }) {
  const th = useTheme();
  return (
    <View style={{ flex: 1 }}>
      <Text style={[th.font.display(500), { fontSize: 22, color: th.c.ink }]}>{value}</Text>
      <T v="tiny" style={{ fontSize: 11 }}>{label}</T>
    </View>
  );
}

function HistoryCard() {
  const { t } = useI18n();
  const { data, error, loading, refetch } = useRemedyHistory();
  return (
    <Card radius={18} pad={16} style={{ marginTop: 14 }}>
      <T v="eyebrow" style={{ marginBottom: 12 }}>{t('remedies.heatTitle')}</T>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {data ? (
        <>
          <Row gap={10} style={{ marginBottom: 14 }}>
            <Stat value={data.totals.active_days} label={t('remedies.activeDays')} />
            <Stat value={data.totals.completions} label={t('remedies.completions')} />
            <Stat value={data.totals.best_streak} label={t('remedies.bestStreak')} />
          </Row>
          <Heatmap days={data.days} />
        </>
      ) : null}
    </Card>
  );
}

/** Full streak panel (Progress tab). */
function StreakPanel({ streak }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  return (
    <GradientPanel style={{ paddingVertical: 18, paddingHorizontal: 20 }}>
      <Row align="flex-end" style={{ justifyContent: 'space-between' }}>
        <View>
          <Text style={[th.font.ui(500), { fontSize: 11, letterSpacing: 1, textTransform: 'uppercase', color: th.c.onAccent, opacity: 0.8 }]}>{t('remedies.streak')}</Text>
          <Text style={[th.font.display(500), { fontSize: 36, lineHeight: 40, color: th.c.onAccent, marginTop: 4 }]}>
            {streak.current} <Text style={{ fontSize: 16 }}>{t('remedies.days')}</Text>
          </Text>
        </View>
        <Text style={[th.font.ui(400), { fontSize: 12, color: th.c.onAccent, opacity: 0.85 }]}>{t('remedies.best', { n: streak.best })}</Text>
      </Row>
      <Row gap={6} style={{ marginTop: 16 }}>
        {streak.week.map((d, i) => (
          <View key={d.date} style={{
            flex: 1, height: 30, borderRadius: 8, alignItems: 'center', justifyContent: 'center',
            backgroundColor: d.done ? 'rgba(255,255,255,.22)' : 'rgba(255,255,255,.09)',
          }}>
            <Text style={[th.font.ui(600), { fontSize: 10, color: d.done ? th.c.onAccent : 'rgba(255,248,238,.5)' }]}>{DAY_LETTERS[lang][i]}</Text>
          </View>
        ))}
      </Row>
    </GradientPanel>
  );
}

/** Compact streak card for the Today tab: streak + the last 13 weeks as a mini heatmap; opens Progress. */
function StreakLine({ streak, days, onPress }) {
  const th = useTheme();
  const { t } = useI18n();
  return (
    <Pressable onPress={onPress} accessibilityRole="button" style={({ pressed }) => ({
      flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 11, paddingHorizontal: 14, borderRadius: 14,
      backgroundColor: th.soft(0.08), opacity: pressed ? 0.8 : 1,
    })}>
      <View style={{ flex: 1 }}>
        <Text style={[th.font.ui(700), { fontSize: 15, color: th.c.accentDark }]}>{t('remedies.streakLine', { n: streak.current })}</Text>
        <T v="tiny" style={{ fontSize: 10.5, marginTop: 2 }}>{t('remedies.bestDays', { n: streak.best })}</T>
        <T v="tiny" style={{ fontSize: 10.5, marginTop: 6, color: th.c.accentDark }}>{t('remedies.seeProgress')}</T>
      </View>
      <View style={{ alignItems: 'flex-end', gap: 4 }}>
        <MiniHeatmap days={days} />
        <T v="tiny" style={{ fontSize: 9, color: th.c.ink3 }}>{t('remedies.last3Months')}</T>
      </View>
    </Pressable>
  );
}

export default function Remedies() {
  const th = useTheme();
  const { t, tr, lang } = useI18n();
  const router = useRouter();
  const { profileId } = useAccount();
  const { data, error, loading, refreshing, refetch } = useRemedies();
  const history = useRemedyHistory();
  const [tab, setTab] = useState('today'); // today: what to do now · progress: streak, heatmap, mood
  // Progress is pre-rendered (hidden) once Today has settled, then kept mounted, so switching tabs
  // never rebuilds the heatmap and charts.
  const [progressReady, setProgressReady] = useState(false);
  useEffect(() => {
    // Idle time after Today has drawn; fall back to a short timeout where idle callbacks are missing.
    if (typeof requestIdleCallback === 'function') {
      const id = requestIdleCallback(() => setProgressReady(true), { timeout: 1500 });
      return () => cancelIdleCallback(id);
    }
    const id = setTimeout(() => setProgressReady(true), 300);
    return () => clearTimeout(id);
  }, []);
  const showTab = (v) => { if (v === 'progress') setProgressReady(true); setTab(v); };
  const key = `remedies:${profileId}:${lang}`;

  if (loading) return <Screen><Loading /></Screen>;
  if (!data) return <Screen><ErrorView error={error} onRetry={refetch} /></Screen>;

  const focus = data.focus[0];
  const goals = data.goals.map((g) => g.label.toLowerCase()).join(', ');
  const setToday = (id, today) => updateCached(key, (d) => ({
    ...d, remedies: d.remedies.map((x) => (x.id === id ? { ...x, today } : x)),
  }));

  // Mark today's remedy done (free); tapping again undoes it. Editing is Pro.
  const markDone = async (r) => {
    const completed = !r.today.completed;
    setToday(r.id, { count: completed ? r.target : 0, completed });
    if (completed) Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    try {
      const res = await remediesApi.progress(r.id, completed ? { completed: true, today: todayISO() }
        : { completed: false, count: 0, today: todayISO() });
      updateCached(key, (d) => ({ ...d, streak: res.streak, remedies: d.remedies.map((x) => (x.id === r.id ? res.remedy : x)) }));
      invalidate(`remedy:${r.id}:`);
      // Refresh the charts in the background, keeping what's drawn (no spinner, no redraw flash).
      invalidate('remedy-history:', { keep: true });
      invalidate('trends:', { keep: true });
    } catch (e) {
      setToday(r.id, r.today);
      Alert.alert(t('common.unknownError'), e.message);
    }
  };

  const refresh = () => { refetch(); history.refetch(); invalidate('journal:'); invalidate('trends:'); };
  const dueToday = data.remedies.filter((r) => r.due_today);
  const doneToday = dueToday.filter((r) => r.today.completed).length;

  return (
    <Screen refreshing={refreshing} onRefresh={refresh}>
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingTop: 8, paddingBottom: 3 }}>{t('remedies.title')}</T>
      {goals ? <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 12 }} numberOfLines={2}>{t('remedies.subGoals', { goals })}</T>
        : focus ? <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 12 }}>{t('remedies.sub', { planet: tr('graha', focus.code) })}</T> : null}

      <Seg value={tab} onChange={showTab} style={{ marginBottom: 14 }}
        options={[{ value: 'today', label: t('remedies.tabToday') }, { value: 'progress', label: t('remedies.tabProgress') }]} />

      <View style={{ display: tab === 'today' ? 'flex' : 'none' }}>
        <StreakLine streak={data.streak} days={history.data?.days} onPress={() => showTab('progress')} />

        {/* The daily log lives here, next to the practice it reflects on. */}
        {brand.features.journal ? <MoodCheckIn /> : null}

        <Row style={{ justifyContent: 'space-between', marginTop: 18, marginBottom: 9, paddingHorizontal: 2 }}>
          <T v="eyebrow">{t('remedies.todayList')}</T>
          {dueToday.length ? <T v="mono" style={{ fontSize: 10.5 }}>{t('remedies.doneCount', { done: doneToday, due: dueToday.length })}</T> : null}
        </Row>
        {!data.remedies.length ? <Empty title={t('remedies.title')} /> : null}
        <View style={{ gap: 8 }}>
          {data.remedies.map((r) => (
            <RemedyCard key={r.id} remedy={r}
              onPress={() => router.push(`/remedies/${r.id}`)}
              right={(
                <Row gap={2} align="flex-start">
                  <EditButton locked={data.locked} onPress={() => router.push(data.locked ? '/paywall' : `/remedies/edit/${r.id}`)} />
                  <DoneButton remedy={r} onPress={() => markDone(r)} />
                </Row>
              )} />
          ))}
        </View>

        <Pressable onPress={() => router.push(data.locked ? '/paywall' : '/remedies/new')} style={{
          flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, padding: 13, borderRadius: 16,
          borderWidth: 1.5, borderStyle: 'dashed', borderColor: th.c.hair2, marginTop: 12,
        }}>
          <Text style={{ fontSize: 18, color: th.c.ink2 }}>+</Text>
          <T weight={600} style={{ fontSize: 14, color: th.c.ink2 }}>{t('remedies.add')}</T>
          {data.locked ? <T v="tiny" style={{ color: th.c.accent }}>◆ {t('common.pro')}</T> : null}
        </Pressable>
        {data.locked ? <T v="tiny" style={{ textAlign: 'center', marginTop: 10 }}>{t('remedies.lockedSub')}</T> : null}
      </View>
      {progressReady ? (
        <View style={{ display: tab === 'progress' ? 'flex' : 'none' }}>
          <StreakPanel streak={data.streak} />
          <HistoryCard />
          {brand.features.journal ? <MoodPractice /> : null}
        </View>
      ) : null}
    </Screen>
  );
}
