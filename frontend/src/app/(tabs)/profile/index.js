import { useRouter } from 'expo-router';
import { Alert, Pressable, Text, View } from 'react-native';

import { profilesApi } from '../../../api/endpoints';
import { Avatar, ErrorView, Loading, Row, Screen, T } from '../../../components/ui';
import { brand } from '../../../config/env';
import { invalidate } from '../../../hooks/useApi';
import { useAccount, useBilling, useGoals, useProfiles } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { useAuth } from '../../../state/AuthContext';
import { useTheme } from '../../../theme';
import { fullDate, initials } from '../../../utils/format';

const AVATAR_COLORS = ['#5E8A6B', '#7C6B9E', '#B05A44', '#566579', '#B08A3A'];

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

  const activate = async (p) => {
    if (p.id === profileId) return;
    try {
      await updateMe({ active_profile_id: p.id });
      invalidate('remedies:');
    } catch (e) {
      Alert.alert(t('common.unknownError'), e.message);
    }
  };

  const actions = (p) => Alert.alert(p.name, undefined, [
    { text: t('common.edit'), onPress: () => router.push(`/profile/edit/${p.id}`) },
    {
      text: t('common.delete'), style: 'destructive',
      onPress: () => Alert.alert(t('common.delete'), t('profiles.deleteConfirm', { name: p.name }), [
        { text: t('common.cancel'), style: 'cancel' },
        {
          text: t('common.delete'), style: 'destructive', onPress: async () => {
            await profilesApi.remove(p.id);
            invalidate(`p:${p.id}`);
            refetch();
            refreshUser();
          },
        },
      ]),
    },
    { text: t('common.cancel'), style: 'cancel' },
  ]);

  const profiles = data?.results || [];
  const b = billing.data;

  return (
    <Screen refreshing={refreshing} onRefresh={refetch}>
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingTop: 8, paddingBottom: 3 }}>{t('profiles.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 18 }}>{t('profiles.sub')}</T>
      {loading ? <Loading /> : null}
      <ErrorView error={error} onRetry={refetch} />
      {profiles.map((p, i) => {
        const active = p.id === profileId;
        return (
          <Pressable key={p.id} onPress={() => activate(p)} onLongPress={() => actions(p)} style={{
            flexDirection: 'row', alignItems: 'center', gap: 13, padding: 13, borderRadius: 16, marginBottom: 9, borderWidth: 1,
            borderColor: active ? th.c.accent : th.c.hair, backgroundColor: active ? th.soft(0.05) : th.c.surface,
          }}>
            <Avatar initials={initials(p.name)} color={p.relation === 'self' ? th.c.accent : AVATAR_COLORS[i % AVATAR_COLORS.length]} />
            <View style={{ flex: 1 }}>
              <Row gap={8}>
                <T weight={600} style={{ fontSize: 15, flexShrink: 1 }} numberOfLines={1}>{p.name}</T>
                <View style={{ paddingVertical: 2, paddingHorizontal: 7, borderRadius: 20, backgroundColor: th.c.muted }}>
                  <T v="tiny" style={{ fontSize: 10, color: th.c.ink2 }}>{t(`relation.${p.relation}`)}</T>
                </View>
              </Row>
              <T v="tiny" style={{ fontSize: 11.5, marginTop: 2 }} numberOfLines={1}>
                {fullDate(p.birth_date, lang)} · {(p.place_label || '').split(',')[0]}
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
      {profiles.length > 1 ? <T v="tiny" style={{ textAlign: 'center', marginTop: 10 }}>{t('profiles.editHint')}</T> : null}

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
          <MenuRow glyph="◆" title={t('profiles.pro')} last
            sub={b?.is_pro ? (b.on_trial ? t('profiles.trialEnds', { date: fullDate(b.trial_ends_at, lang) }) : t('profiles.proActive')) : undefined}
            onPress={() => router.push('/paywall')} />
        ) : null}
      </View>
    </Screen>
  );
}
