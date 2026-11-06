import { useRouter } from 'expo-router';

import { profilesApi } from '../../api/endpoints';
import { ProfileForm } from '../../components/ProfileForm';
import { invalidate } from '../../hooks/useApi';
import { useI18n } from '../../i18n';
import { useAuth } from '../../state/AuthContext';

export default function NewProfile() {
  const router = useRouter();
  const { t } = useI18n();
  const { user, refreshUser } = useAuth();
  return (
    <ProfileForm
      title={t('form.newTitle')}
      onSubmit={async (body) => {
        const p = await profilesApi.create(body);
        invalidate('profiles');
        if (!user?.active_profile_id) await refreshUser(); // first chart becomes the active one
        // Goals belong to each chart: pick this one's now, or skip.
        router.replace({ pathname: '/goals', params: { profile: p.id, isNew: '1' } });
      }}
    />
  );
}
