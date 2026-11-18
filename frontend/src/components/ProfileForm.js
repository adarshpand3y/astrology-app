import { useRouter } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, Text, View } from 'react-native';

import { brand } from '../config/env';
import { useI18n } from '../i18n';
import { useAuth } from '../state/AuthContext';
import { useTheme } from '../theme';
import { fieldErrors, fromApiDateTime, toApiDate, toApiTime } from '../utils/format';
import { DateTimeField } from './DateTimeField';
import { LocationPicker } from './LocationPicker';
import { ExperiencePicker } from './Preferences';
import { Button, Chip, ErrorView, Field, Row, Screen, Seg, T } from './ui';

const RELATIONS = ['self', 'family', 'friend', 'client', 'other'];

/** Create/edit a birth profile. `initial` is a backend profile (edit) or undefined (create). */
export function ProfileForm({ initial, title, onSubmit }) {
  const th = useTheme();
  const { t } = useI18n();
  const router = useRouter();
  const { user } = useAuth();
  const [name, setName] = useState(initial?.name || '');
  const [relation, setRelation] = useState(initial?.relation || 'family');
  const [gender, setGender] = useState(initial?.gender || '');
  const [dob, setDob] = useState(() => (initial ? fromApiDateTime(initial.birth_date, initial.birth_time) : null));
  const [tob, setTob] = useState(() => (initial ? fromApiDateTime(initial.birth_date, initial.birth_time) : null));
  const [place, setPlace] = useState(initial ? { id: initial.place_id, label: initial.place_label } : null);
  // Asked again when adding a chart (account-wide; pre-filled with the current level).
  const [experience, setExperience] = useState(user?.experience || 'advanced');
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const server = fieldErrors(error);

  const submit = async () => {
    setTried(true);
    if (!name.trim() || !dob || !tob || !place) return;
    const body = {
      name: name.trim(), relation, gender, birth_date: toApiDate(dob), birth_time: toApiTime(tob),
      ayanamsa: brand.defaults.ayanamsa,
    };
    if (!initial || (place.id && place.id !== initial.place_id)) body.place_id = place.id;
    setBusy(true);
    setError(null);
    try {
      await onSubmit(body, initial ? {} : { experience });
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: th.c.bg }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen tabs={false}>
        <Row style={{ justifyContent: 'space-between', paddingTop: 6, paddingBottom: 16 }}>
          <T v="screenTitle">{title}</T>
          <Pressable onPress={() => router.back()} hitSlop={10} style={{ width: 30, height: 30, borderRadius: 15, backgroundColor: th.c.muted, alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ color: th.c.ink2 }}>✕</Text>
          </Pressable>
        </Row>
        {!Object.keys(server).length ? <ErrorView error={error} /> : null}
        <View style={{ gap: 14 }}>
          <Field label={t('form.name')} value={name} onChangeText={setName}
            error={tried && !name.trim() ? t('auth.nameRequired') : server.name} />
          <View>
            <T v="label" style={{ marginBottom: 8 }}>{t('form.relation')}</T>
            <Row gap={8} style={{ flexWrap: 'wrap' }}>
              {RELATIONS.map((r) => <Chip key={r} label={t(`relation.${r}`)} active={relation === r} onPress={() => setRelation(r)} />)}
            </Row>
          </View>
          <View>
            <T v="label" style={{ marginBottom: 8 }}>{t('form.gender')}</T>
            <Seg value={gender} onChange={setGender} options={['male', 'female', 'other'].map((g) => ({ value: g, label: t(`form.${g}`) }))} />
          </View>
          <Row gap={11} align="flex-start">
            <DateTimeField label={t('form.birthDate')} value={dob} onChange={setDob} style={{ flex: 1.2 }}
              error={tried && !dob ? t('auth.dateRequired') : null} />
            <DateTimeField label={t('auth.time')} mode="time" value={tob} onChange={setTob}
              error={tried && !tob ? t('auth.timeRequired') : null} style={{ flex: 1 }} />
          </Row>
          {server.birth_date || server.birth_time ? <T v="caption" style={{ color: th.kind.bad.solid }}>{server.birth_date || server.birth_time}</T> : null}
          <LocationPicker label={t('form.place')} value={place?.label ? place : null} onChange={setPlace}
            error={tried && !place ? t('auth.placeRequired') : null} />
          {!initial ? (
            <View>
              <T v="label" style={{ marginBottom: 4 }}>{t('experience.question')}</T>
              <T v="caption" style={{ marginBottom: 10 }}>{t('experience.sub')}</T>
              <ExperiencePicker value={experience} onChange={setExperience} />
            </View>
          ) : null}
        </View>
        <Button title={t('form.save')} onPress={submit} loading={busy} style={{ marginTop: 24 }} />
      </Screen>
    </KeyboardAvoidingView>
  );
}
