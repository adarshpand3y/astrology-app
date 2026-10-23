import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Text, View } from 'react-native';

import { profilesApi } from '../../api/endpoints';
import { DateTimeField } from '../../components/DateTimeField';
import { LocationPicker } from '../../components/LocationPicker';
import { OnboardingScreen } from '../../components/Onboarding';
import { Button, Checkbox, ErrorView, Field, Row, T } from '../../components/ui';
import { brand } from '../../config/env';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';
import { useTheme } from '../../theme';
import { fieldErrors, toApiDate, toApiTime } from '../../utils/format';

/** Onboarding step 1: the user's own birth details and where they live now. */
export default function OnboardingProfile() {
  const { t } = useI18n();
  const th = useTheme();
  const router = useRouter();
  const { user, updateMe } = useAuth();
  const [name, setName] = useState(user?.full_name || '');
  const [dob, setDob] = useState(null);
  const [tob, setTob] = useState(null);
  const [timeUnknown, setTimeUnknown] = useState(false);
  const [birthPlace, setBirthPlace] = useState(null);
  const [livePlace, setLivePlace] = useState(user?.current_place ? { id: user.current_place.id, label: user.current_place.label } : null);
  const [created, setCreated] = useState(false);
  const [tried, setTried] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const server = fieldErrors(error);

  const errs = tried ? {
    name: !name.trim() ? t('auth.nameRequired') : server.name,
    dob: !dob ? t('auth.dateRequired') : server.birth_date,
    tob: !tob && !timeUnknown ? t('auth.timeRequired') : server.birth_time,
    birthPlace: !birthPlace ? t('auth.placeRequired') : server.place_id,
    livePlace: !livePlace ? t('auth.placeRequired') : server.current_place_id,
  } : {};

  const submit = async () => {
    setTried(true);
    if (!name.trim() || !dob || (!tob && !timeUnknown) || !birthPlace || !livePlace) return;
    setBusy(true);
    setError(null);
    try {
      if (!user?.active_profile_id && !created) {
        await profilesApi.create({
          name: name.trim(), relation: 'self', birth_date: toApiDate(dob),
          birth_time: timeUnknown ? null : toApiTime(tob), time_known: !timeUnknown, place_id: birthPlace.id,
          node_mode: brand.defaults.nodeMode, ayanamsa: brand.defaults.ayanamsa,
        });
        setCreated(true); // don't create a second chart if saving the place fails and the user retries
      }
      // The first chart becomes the active one; this also refreshes the user.
      await updateMe({ full_name: name.trim(), current_place_id: livePlace.id });
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
          <DateTimeField label={t('auth.time')} mode="time" value={tob} onChange={setTob} disabled={timeUnknown} error={errs.tob}
            display={timeUnknown ? t('auth.unknown') : undefined} style={{ flex: 1 }} />
        </Row>
        <View style={{ marginTop: -3 }}>
          <Checkbox checked={timeUnknown} onChange={setTimeUnknown}>
            <T v="small">
              {t('auth.timeUnknown')}<Text style={{ color: th.c.ink3 }}>{t('auth.timeUnknownHint')}</Text>
            </T>
          </Checkbox>
        </View>
        <LocationPicker label={t('auth.birthPlace')} icon="pin" value={birthPlace} onChange={setBirthPlace} error={errs.birthPlace} />
        <LocationPicker label={t('auth.livePlace')} hint={t('auth.livePlaceHint')} icon="target" value={livePlace}
          onChange={setLivePlace} error={errs.livePlace} />
      </View>
      <Button title={t('onboarding.profileCta')} onPress={submit} loading={busy} style={{ marginTop: 24, paddingVertical: 16 }} />
    </OnboardingScreen>
  );
}
