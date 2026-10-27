import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, Text, TextInput, View } from 'react-native';

import { journalApi } from '../../../api/endpoints';
import { MOOD_GLYPHS, MoodGlyph } from '../../../components/MoodCheckIn';
import { BackLink, Button, ErrorView, Loading, Row, Screen, T } from '../../../components/ui';
import { invalidate } from '../../../hooks/useApi';
import { useJournalDay } from '../../../hooks/data';
import { useI18n } from '../../../i18n';
import { requireOnline } from '../../../network';
import { useTheme } from '../../../theme';
import { shortDate, todayISO } from '../../../utils/format';

const GLYPHS = MOOD_GLYPHS;

/** Today's log in full (rating, tags, note); the quick check-in on the Remedies page covers the rating. */
export default function Journal() {
  const today = todayISO();
  const { data, loading, error, refetch } = useJournalDay(today);
  if (loading) return <Screen><Loading /></Screen>;
  if (!data) return <Screen><ErrorView error={error} onRetry={refetch} /></Screen>;
  return <JournalForm data={data} today={today} />;
}

function JournalForm({ data, today }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const entry = data.entry;
  const [rating, setRating] = useState(entry?.rating ?? null);
  const [tags, setTags] = useState(entry?.tags || []);
  const [custom, setCustom] = useState((entry?.tags || []).filter((x) => !data.suggested_tags.includes(x)));
  const [note, setNote] = useState(entry?.note || '');
  const [adding, setAdding] = useState(false);
  const [newTag, setNewTag] = useState('');
  const [busy, setBusy] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const allTags = [...(data?.suggested_tags || []), ...custom];
  const toggleTag = (x) => setTags((cur) => (cur.includes(x) ? cur.filter((y) => y !== x) : [...cur, x]));

  const save = async () => {
    if (!rating) { setSaveError({ message: t('journal.pickRating') }); return; }
    if (!requireOnline(t)) return;
    setBusy(true);
    setSaveError(null);
    try {
      await journalApi.save(today, { rating, tags, note }, today);
      invalidate('journal:');
      invalidate('trends:');
      router.back(); // the Remedies page shows the mood & practice chart
    } catch (e) {
      setSaveError(e);
    } finally {
      setBusy(false);
    }
  };

  const ratings = t('journal.ratings');
  return (
    <Screen>
      <BackLink label={t('remedies.title')} />
      <T v="screenTitle" style={{ paddingHorizontal: 2, paddingBottom: 3 }}>{t('journal.title')}</T>
      <T v="small" style={{ paddingHorizontal: 2, paddingBottom: 18 }}>{t('journal.sub', { date: shortDate(today, lang) })}</T>

      <T weight={600} style={{ fontSize: 13, marginBottom: 11 }}>{t('journal.feel')}</T>
      <Row gap={8} style={{ marginBottom: 22 }}>
        {GLYPHS.map((g, i) => {
          const val = i + 1;
          const sel = rating === val;
          const color = sel ? th.c.accent : th.c.ink2;
          return (
            <Pressable key={g} onPress={() => setRating(val)} style={{
              flex: 1, alignItems: 'center', gap: 6, paddingVertical: 13, paddingHorizontal: 3, borderRadius: 14, borderWidth: 1,
              borderColor: sel ? th.c.accent : th.c.hair2, backgroundColor: sel ? th.soft(0.08) : th.c.surface,
            }}>
              <MoodGlyph index={i} size={20} color={color} />
              <Text numberOfLines={1} style={[th.font.ui(600), { fontSize: 10, color }]}>{ratings[i]}</Text>
            </Pressable>
          );
        })}
      </Row>

      <T weight={600} style={{ fontSize: 13, marginBottom: 11 }}>{t('journal.shaped')}</T>
      <Row gap={8} style={{ flexWrap: 'wrap', marginBottom: 22 }}>
        {allTags.map((x) => {
          const sel = tags.includes(x);
          return (
            <Pressable key={x} onPress={() => toggleTag(x)} style={{
              paddingVertical: 8, paddingHorizontal: 13, borderRadius: 20, borderWidth: 1,
              borderColor: sel ? th.c.accent : th.c.hair2, backgroundColor: sel ? th.soft(0.09) : th.c.surface,
            }}>
              <Text style={[th.font.ui(400), { fontSize: 12.5, color: sel ? th.c.accentDark : th.c.ink2 }]}>{x}</Text>
            </Pressable>
          );
        })}
        {adding ? (
          <TextInput
            autoFocus
            value={newTag}
            onChangeText={setNewTag}
            placeholder={t('journal.addPh')}
            placeholderTextColor={th.c.ink3}
            maxLength={30}
            onSubmitEditing={() => {
              const v = newTag.trim();
              if (v && !allTags.includes(v)) { setCustom((c) => [...c, v]); setTags((c) => [...c, v]); }
              setNewTag('');
              setAdding(false);
            }}
            onBlur={() => setAdding(false)}
            style={[th.font.ui(400), {
              minWidth: 110, paddingVertical: 7, paddingHorizontal: 13, borderRadius: 20, borderWidth: 1,
              borderColor: th.c.accent, color: th.c.ink, fontSize: 12.5,
            }]}
          />
        ) : (
          <Pressable onPress={() => setAdding(true)} style={{
            paddingVertical: 8, paddingHorizontal: 13, borderRadius: 20, borderWidth: 1, borderColor: th.c.hair2, backgroundColor: th.c.surface,
          }}>
            <Text style={[th.font.ui(400), { fontSize: 12.5, color: th.c.ink2 }]}>{t('journal.add')}</Text>
          </Pressable>
        )}
      </Row>

      <View style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair2, borderRadius: 16, padding: 15, minHeight: 96 }}>
        <TextInput
          value={note}
          onChangeText={setNote}
          multiline
          placeholder={t('journal.notePh')}
          placeholderTextColor={th.c.ink3}
          maxLength={4000}
          style={[th.font.ui(400), { fontSize: 13.5, color: th.c.ink, minHeight: 66, textAlignVertical: 'top', padding: 0 }]}
        />
      </View>
      <ErrorView error={saveError} style={{ marginTop: 12 }} />
      <Button title={t('journal.save')} onPress={save} loading={busy} style={{ marginTop: 16 }} />
    </Screen>
  );
}
