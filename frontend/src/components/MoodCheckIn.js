import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text } from 'react-native';

import { journalApi } from '../api/endpoints';
import { useJournalDay } from '../hooks/data';
import { invalidate, setCached } from '../hooks/useApi';
import { useI18n } from '../i18n';
import { requireOnline } from '../network';
import { useTheme } from '../theme';
import { todayISO } from '../utils/format';
import { Icon, MOOD_ICONS } from './Icons';
import { Card, ErrorView, Row, T } from './ui';

/** Heavy → Bright (ratings 1–5); vector icons so all five are the same size. */
export const MOOD_GLYPHS = MOOD_ICONS;

/** One mood icon (`index` 0–4). */
export function MoodGlyph({ index, size, color }) {
  return <Icon name={MOOD_ICONS[index]} size={Math.round(size * 1.2)} color={color} />;
}

/**
 * One-tap daily mood check-in for the Remedies page. Saves today's rating right away, keeping any
 * tags/note already logged; "Add a note" opens the full log screen.
 */
export function MoodCheckIn() {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const today = todayISO();
  const key = `journal:${today}:${lang}`;
  const { data, error, refetch } = useJournalDay(today);
  const [saveError, setSaveError] = useState(null);
  const entry = data?.entry;
  const ratings = t('journal.ratings');

  const pick = async (rating) => {
    if (!data || entry?.rating === rating || !requireOnline(t)) return;
    const body = { rating, tags: entry?.tags || [], note: entry?.note || '' };
    setCached(key, { ...data, entry: { ...(entry || {}), ...body } });
    setSaveError(null);
    try {
      await journalApi.save(today, body, today);
      invalidate('trends:', { keep: true }); // refresh the mood chart without a spinner
    } catch (e) {
      setCached(key, data);
      setSaveError(e);
    }
  };

  return (
    <Card radius={18} pad={16} style={{ marginTop: 14 }}>
      <Row style={{ justifyContent: 'space-between', marginBottom: 12 }}>
        <T weight={600} style={{ fontSize: 14 }}>{t('journal.checkIn')}</T>
        <Pressable onPress={() => router.push('/remedies/journal')} hitSlop={8}>
          <T v="link" style={{ fontSize: 12.5 }}>{entry?.note || entry?.tags?.length ? t('journal.editNote') : t('journal.addNote')}</T>
        </Pressable>
      </Row>
      {!data && error ? <ErrorView error={error} onRetry={refetch} /> : null}
      <Row gap={6}>
        {MOOD_GLYPHS.map((g, i) => {
          const val = i + 1;
          const sel = entry?.rating === val;
          const color = sel ? th.c.accent : th.c.ink2;
          return (
            <Pressable key={g} onPress={() => pick(val)} disabled={!data}
              accessibilityRole="radio" accessibilityState={{ checked: sel }} accessibilityLabel={ratings[i]}
              style={({ pressed }) => ({
                flex: 1, alignItems: 'center', gap: 4, paddingVertical: 10, borderRadius: 12, borderWidth: 1,
                borderColor: sel ? th.c.accent : th.c.hair2, backgroundColor: sel ? th.soft(0.08) : th.c.surface,
                opacity: !data ? 0.5 : pressed ? 0.8 : 1,
              })}>
              <MoodGlyph index={i} size={18} color={color} />
              <Text numberOfLines={1} style={[th.font.ui(600), { fontSize: 9.5, color }]}>{ratings[i]}</Text>
            </Pressable>
          );
        })}
      </Row>
      {entry ? <T v="caption" style={{ marginTop: 9 }}>{t('journal.logged')}</T> : null}
      <ErrorView error={saveError} style={{ marginTop: 8 }} />
    </Card>
  );
}
