import { useRouter } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';

import { profilesApi } from '../../api/endpoints';
import { DateTimeField } from '../../components/DateTimeField';
import { LocationPicker } from '../../components/LocationPicker';
import { OnboardingScreen } from '../../components/Onboarding';
import { ExperiencePicker } from '../../components/Preferences';
import { Button, ErrorView, Field, Row, T } from '../../components/ui';
import { brand } from '../../config/env';
import { invalidate } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { fieldErrors, toApiDate, toApiTime } from '../../utils/format';

/** Onboarding step 1: the user's own birth details and where they live now. */
export default function OnboardingProfile() {
  const { t } = useI18n();
  const router = useRouter();
  const { user, updateMe } = useAuth();
  const [name, setName] = useState(user?.full_name || '');
  const [dob, setDob] = useState(null);
  const [tob, setTob] = useState(null);
  const [birthPlace, setBirthPlace] = useState(null);
  const [livePlace, setLivePlace] = useState(user?.current_place ? { id: user.current_place.id, label: user.current_place.label } : null);
  const [experience, setExperience] = useState(user?.experience || '');
  const [created, setCreated] = useState(false);
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const server = fieldErrors(error);

  const errs = tried ? {
    name: !name.trim() ? t('auth.nameRequired') : server.name,
    dob: !dob ? t('auth.dateRequired') : server.birth_date,
    tob: !tob ? t('auth.timeRequired') : server.birth_time,
    birthPlace: !birthPlace ? t('auth.placeRequired') : server.place_id,
    livePlace: !livePlace ? t('auth.placeRequired') : server.current_place_id,
    experience: !experience ? t('experience.required') : server.experience,
  } : {};

  const submit = async () => {
    setTried(true);
    if (!name.trim() || !dob || !tob || !birthPlace || !livePlace || !experience) return;
    setBusy(true);
    setError(null);
    try {
      if (!user?.active_profile_id && !created) {
        await profilesApi.create({
          name: name.trim(), relation: 'self', birth_date: toApiDate(dob),
          birth_time: toApiTime(tob), place_id: birthPlace.id,
          ayanamsa: brand.defaults.ayanamsa,
        });
        setCreated(true); // don't create a second chart if saving the place fails and the user retries
        // A saved (possibly empty) chart list from before, e.g. after deleting the last chart, is out of date.
        invalidate('profiles');
      }
      // The first chart becomes the active one; this also refreshes the user.
      await updateMe({ full_name: name.trim(), current_place_id: livePlace.id, experience });
      router.replace('/onboarding/goals');
    } catch (e) {
      setError(e);
      setBusy(false);
    }
  };

  return (
    <OnboardingScreen step={1} title={t('onboarding.profileTitle')} sub={t('onboarding.profileSub')}>
      {!Object.keys(server).length ? <ErrorView error={error} /> : null}
      <View style={{ gap: 14, marginTop: 6 }}>
        <Field label={t('auth.name')} value={name} onChangeText={setName} placeholder={t('auth.namePh')} autoComplete="name" error={errs.name} />
        <Row gap={11} align="flex-start">
          <DateTimeField label={t('auth.dob')} value={dob} onChange={setDob} error={errs.dob} style={{ flex: 1.2 }} />
          <DateTimeField label={t('auth.time')} mode="time" value={tob} onChange={setTob} error={errs.tob} style={{ flex: 1 }} />
        </Row>
        <LocationPicker label={t('auth.birthPlace')} icon="pin" value={birthPlace} onChange={setBirthPlace} error={errs.birthPlace} />
        <LocationPicker label={t('auth.livePlace')} hint={t('auth.livePlaceHint')} icon="target" value={livePlace}
          onChange={setLivePlace} error={errs.livePlace} />
        <View>
          <T v="label" style={{ marginBottom: 4 }}>{t('experience.question')}</T>
          <T v="caption" style={{ marginBottom: 10 }}>{t('experience.sub')}</T>
          <ExperiencePicker value={experience} onChange={setExperience} error={errs.experience} />
        </View>
      </View>
      <Button title={t('onboarding.profileCta')} onPress={submit} loading={busy} style={{ marginTop: 24, paddingVertical: 16 }} />
    </OnboardingScreen>
  );
}
