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
        await profilesApi.create(body);
        invalidate('profiles');
        if (!user?.active_profile_id) await refreshUser(); // first chart becomes the active one
        router.back();
      }}
    />
  );
}
