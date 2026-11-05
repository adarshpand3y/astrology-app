import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Alert, Pressable, Text, View } from 'react-native';

import { profilesApi } from '../../../api/endpoints';
import { ProIcon } from '../../../components/Icons';
import { Avatar, Button, ErrorView, Loading, Row, Screen, Sheet, T } from '../../../components/ui';
import { brand } from '../../../config/env';
import { invalidate } from '../../../hooks/useApi';
import { useAccount, useBilling, useGoals, useProfiles } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useAuth } from '../../../state/AuthContext';
import { ERROR, useTheme } from '../../../theme';
import { clock, errorMessage, fullDate, initials } from '../../../utils/format';

const AVATAR_COLORS = ['#5E8A6B', '#7C6B9E', '#B05A44', '#566579', '#B08A3A'];

const avatarColor = (p, i, th) => (p.relation === 'self' ? th.c.accent : AVATAR_COLORS[i % AVATAR_COLORS.length]);

/** "3:42 AM", or "time unknown" when the chart was cast without a birth time. */
function birthTime(p, t, lang) {
  if (!p.time_known || !p.birth_time) return t('profiles.noTime');
  const [h, m] = p.birth_time.split(':');
  return clock(`2000-01-01T${h}:${m}`, lang, true);
}

/** One action in the chart sheet: icon tile, label, optional note. */
function SheetAction({ glyph, title, sub, onPress, danger }) {
  const th = useTheme();
  const color = danger ? ERROR : th.c.accent;
  return (
    <Pressable onPress={onPress} accessibilityRole="button" style={({ pressed }) => ({
      flexDirection: 'row', alignItems: 'center', gap: 13, paddingVertical: 12, paddingHorizontal: 4,
      borderRadius: 12, backgroundColor: pressed ? th.c.muted : 'transparent',
    })}>
      <View style={{
        width: 38, height: 38, borderRadius: 11, alignItems: 'center', justifyContent: 'center',
        backgroundColor: danger ? 'rgba(192,57,43,.1)' : th.soft(0.13),
      }}>
        <Text style={{ color, fontSize: 16 }}>{glyph}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <T weight={600} style={{ fontSize: 15, color: danger ? ERROR : th.c.ink }}>{title}</T>
        {sub ? <T v="caption" style={{ marginTop: 1 }}>{sub}</T> : null}
      </View>
    </Pressable>
  );
}

/**
 * Bottom sheet for a chart: who it is (birth details), then use / edit / delete. Delete asks to
 * confirm in place, and an error stays in the sheet.
 */
function ChartSheet({ profile: p, color, active, onClose, onActivate, onEdit, onDeleted }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const reset = () => { setConfirming(false); setErr(null); };
  const close = () => { if (!busy) { reset(); onClose(); } };
  const remove = async () => {
    setBusy(true);
    setErr(null);
    try {
      await profilesApi.remove(p.id);
      reset();
      onDeleted(p);
    } catch (e) {
      setErr(errorMessage(e, t));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Sheet visible={!!p} onClose={close}>
      {p ? (
        <>
          <Row gap={13} align="flex-start">
            <Avatar initials={initials(p.name)} color={color} size={48} />
            <View style={{ flex: 1 }}>
              <Row gap={8}>
                <T weight={600} style={{ fontSize: 17, flexShrink: 1 }} numberOfLines={1}>{p.name}</T>
                <View style={{ paddingVertical: 2, paddingHorizontal: 7, borderRadius: 20, backgroundColor: th.c.muted }}>
                  <T v="tiny" style={{ fontSize: 10, color: th.c.ink2 }}>{t(`relation.${p.relation}`)}</T>
                </View>
              </Row>
              <T v="caption" style={{ marginTop: 3 }}>{fullDate(p.birth_date, lang)} · {birthTime(p, t, lang)}</T>
              {p.place_label ? <T v="caption" numberOfLines={2}>{p.place_label}</T> : null}
            </View>
          </Row>
          <View style={{ height: 1, backgroundColor: th.c.hair, marginVertical: 14 }} />

          {confirming ? (
            <View>
              <T weight={600} style={{ fontSize: 16 }}>{t('profiles.deleteConfirm', { name: p.name })}</T>
              <T v="small" style={{ marginTop: 6 }}>{t(active ? 'profiles.deleteActiveSub' : 'profiles.deleteSub')}</T>
              {err ? <T v="caption" style={{ color: ERROR, marginTop: 10 }}>{err}</T> : null}
              <Row gap={10} style={{ marginTop: 18 }}>
                <Button title={t('common.cancel')} variant="secondary" onPress={reset} disabled={busy} style={{ flex: 1 }} />
                <Button title={t('common.delete')} variant="danger" onPress={remove} loading={busy} style={{ flex: 1 }} />
              </Row>
            </View>
          ) : (
            <View>
              {active ? null : (
                <SheetAction glyph="✓" title={t('profiles.use')} sub={t('profiles.useSub')} onPress={() => { close(); onActivate(p); }} />
              )}
              <SheetAction glyph="✎" title={t('profiles.editAction')} sub={t('profiles.editSub')} onPress={() => { close(); onEdit(p); }} />
              <SheetAction glyph="✕" title={t('profiles.deleteAction')} danger onPress={() => setConfirming(true)} />
              <Button title={t('common.cancel')} variant="secondary" onPress={close} style={{ marginTop: 12 }} />
            </View>
          )}
        </>
      ) : null}
    </Sheet>
  );
}

function MenuRow({ glyph, title, sub, onPress, last }) {
  const th = useTheme();
  return (
    <Pressable onPress={onPress} style={({ pressed }) => ({
      flexDirection: 'row', alignItems: 'center', gap: 13, paddingVertical: 14, paddingHorizontal: 16,
      borderBottomWidth: last ? 0 : 1, borderBottomColor: th.c.hair, backgroundColor: pressed ? th.c.muted : 'transparent',
    })}>
      <View style={{ width: 34, height: 34, borderRadius: 10, backgroundColor: th.soft(0.13), alignItems: 'center', justifyContent: 'center' }}>
        <Text style={{ color: th.c.accent, fontSize: 15 }}>{glyph}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <T weight={600} style={{ fontSize: 14 }}>{title}</T>
        {sub ? <T v="caption" style={{ marginTop: 1 }}>{sub}</T> : null}
      </View>
      <Text style={{ color: th.c.ink3, fontSize: 16 }}>›</Text>
    </Pressable>
  );
}

export default function Profiles() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const { updateMe, refreshUser } = useAuth();
  const { profileId } = useAccount();
  const { data, error, loading, refreshing, refetch } = useProfiles();
  const billing = useBilling();
  const goals = useGoals();
  const [sheet, setSheet] = useState(null); // { profile, index } the action sheet is open for

  const activate = async (p) => {
    if (p.id === profileId) return;
    try {
      await updateMe({ active_profile_id: p.id });
      invalidate('remedies:');
    } catch (e) {
      Alert.alert(t('common.unknownError'), e.message);
    }
  };

  const deleted = (p) => {
    setSheet(null);
    invalidate(`p:${p.id}`);
    refetch();
    refreshUser();
  };

  const profiles = data?.results || [];
  const b = billing.data;

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingTop: 8, paddingBottom: 3 }}>{t('profiles.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 18 }}>{t(profiles.length ? 'profiles.sub' : 'profiles.subEmpty')}</T>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {profiles.map((p, i) => {
        const active = p.id === profileId;
        return (
          <Pressable key={p.id} onPress={() => activate(p)} onLongPress={() => setSheet({ profile: p, index: i })}
            accessibilityHint={t('profiles.editHint')} style={{
            flexDirection: 'row', alignItems: 'center', gap: 13, padding: 13, borderRadius: 16, marginBottom: 9, borderWidth: 1,
            borderColor: active ? th.c.accent : th.c.hair, backgroundColor: active ? th.soft(0.05) : th.c.surface,
          }}>
            <Avatar initials={initials(p.name)} color={avatarColor(p, i, th)} />
            <View style={{ flex: 1 }}>
              <Row gap={8}>
                <T weight={600} style={{ fontSize: 15, flexShrink: 1 }} numberOfLines={1}>{p.name}</T>
                <View style={{ paddingVertical: 2, paddingHorizontal: 7, borderRadius: 20, backgroundColor: th.c.muted }}>
                  <T v="tiny" style={{ fontSize: 10, color: th.c.ink2 }}>{t(`relation.${p.relation}`)}</T>
                </View>
              </Row>
              <T v="tiny" style={{ fontSize: 11.5, marginTop: 2 }} numberOfLines={1}>
                {[fullDate(p.birth_date, lang), birthTime(p, t, lang), (p.place_label || '').split(',')[0]].filter(Boolean).join(' · ')}
              </T>
            </View>
            {active ? (
              <View style={{ width: 22, height: 22, borderRadius: 11, backgroundColor: th.c.accent, alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ color: '#fff', fontSize: 12 }}>✓</Text>
              </View>
            ) : null}
          </Pressable>
        );
      })}
      <Pressable onPress={() => router.push('/profile/new')} style={{
        flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, padding: 15, borderRadius: 16,
        borderWidth: 1.5, borderStyle: 'dashed', borderColor: th.c.hair2, marginTop: 4,
      }}>
        <Text style={{ fontSize: 18, color: th.c.ink2 }}>+</Text>
        <T weight={600} style={{ fontSize: 14, color: th.c.ink2 }}>{t('profiles.add')}</T>
      </Pressable>

      <T v="eyebrow" style={{ marginTop: 26, marginBottom: 10, marginHorizontal: 2 }}>{t('profiles.yourSpace')}</T>
      <View style={{ backgroundColor: th.c.surface, borderRadius: 18, borderWidth: 1, borderColor: th.c.hair, overflow: 'hidden' }}>
        {brand.features.remedies ? (
          <MenuRow glyph="✦" title={t('goals.title')} sub={goals.data?.catalogue
            .filter((g) => goals.data.goals.includes(g.key)).map((g) => g.label).join(' · ')}
            onPress={() => router.push('/goals')} />
        ) : null}
        {brand.features.alerts ? <MenuRow glyph="◈" title={t('profiles.alerts')} onPress={() => router.push('/profile/alerts')} /> : null}
        <MenuRow glyph="⚙" title={t('profiles.settings')} onPress={() => router.push('/profile/settings')} last={!brand.features.paywall} />
        {brand.features.paywall ? (
          <MenuRow glyph={<ProIcon size={16} />} title={t('profiles.pro')} last
            sub={b?.is_pro ? (b.on_trial ? t('profiles.trialEnds', { date: fullDate(b.trial_ends_at, lang) }) : t('profiles.proActive')) : undefined}
            onPress={() => router.push('/paywall')} />
        ) : null}
      </View>

      <ChartSheet
        profile={sheet?.profile}
        color={sheet ? avatarColor(sheet.profile, sheet.index, th) : th.c.accent}
        active={sheet?.profile.id === profileId}
        onClose={() => setSheet(null)}
        onActivate={activate}
        onEdit={(p) => router.push(`/profile/edit/${p.id}`)}
        onDeleted={deleted}
      />
    </Screen>
  );
}
