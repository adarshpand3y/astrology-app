import { useLocalSearchParams, useRouter } from 'expo-router';

import { profilesApi } from '../../../api/endpoints';
import { ProfileForm } from '../../../components/ProfileForm';
import { ErrorView, Loading, Screen } from '../../../components/ui';
import { invalidate, useApi } from '../../../hooks/useApi';
import { useI18n } from '../../../i18n';

export default function EditProfile() {
  const { id } = useLocalSearchParams();
  const router = useRouter();
  const { t } = useI18n();
  const { data, error, loading, refetch } = useApi(`p:${id}`, () => profilesApi.get(id));

  if (loading) return <Screen tabs={false}><Loading /></Screen>;
  if (!data) return <Screen tabs={false}><ErrorView error={error} onRetry={refetch} /></Screen>;

  return (
    <ProfileForm
      initial={data}
      title={t('form.editTitle')}
      onSubmit={async (body) => {
        await profilesApi.update(id, body);
        invalidate(`p:${id}`); // profile + every computed result for it
        invalidate('profiles');
        invalidate('home:');
        router.back();
      }}
    />
  );
}
