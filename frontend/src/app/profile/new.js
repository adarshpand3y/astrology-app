import { useRouter } from 'expo-router';

import { profilesApi } from '../../api/endpoints';
import { ProfileForm } from '../../components/ProfileForm';
import { invalidate } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';

export default function NewProfile() {
  const router = useRouter();
  const { t } = useI18n();
  const { user, refreshUser, updateMe } = useAuth();
  return (
    <ProfileForm
      title={t('form.newTitle')}
      onSubmit={async (body, { experience }) => {
        // The experience level is account-wide. Saved first so a failure here can't leave a duplicate chart on retry.
        if (experience && experience !== user?.experience) await updateMe({ experience });
        const p = await profilesApi.create(body);
        invalidate('profiles');
        if (!user?.active_profile_id) await refreshUser(); // first chart becomes the active one
        // Goals belong to each chart: pick this one's now, or skip.
        router.replace({ pathname: '/goals', params: { profile: p.id, isNew: '1' } });
      }}
    />
  );
}
