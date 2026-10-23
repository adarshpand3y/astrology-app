import { useRouter } from 'expo-router';
import { KeyboardAvoidingView, Platform, Pressable, Text } from 'react-native';

import { remediesApi } from '../api/endpoints';
import { invalidate, setCached, useApi } from '../hooks/useApi';
import { useI18n } from '../i18n';
import { syncSchedule } from '../notifications';
import { useTheme } from '../theme';
import { confirm } from '../utils/confirm';
import { todayISO } from '../utils/format';
import { RemedyForm } from './RemedyForm';
import { ErrorView, Loading, Row, Screen, T } from './ui';

const refreshLists = () => {
  invalidate('remedies:');
  invalidate('onboarding:remedies');
  invalidate('remedy-history:', { keep: true });
  invalidate('trends:', { keep: true });
};

/**
 * Screen for every change to a remedy (Pro): edit text, count, days, reminder, reset or remove an
 * existing remedy (`id`), or create a custom one (`id` undefined). `home` is the list to return to
 * after removing it.
 */
export function RemedyEditScreen({ id, home = '/remedies' }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  const router = useRouter();
  const key = id ? `remedy:${id}:${lang}` : null;
  const { data, error, loading, refetch } = useApi(key, () => remediesApi.get(id, todayISO()));

  const proGate = async (action) => {
    try {
      return await action();
    } catch (e) {
      if (e.code === 'pro_required') { router.replace('/paywall'); return undefined; }
      throw e;
    }
  };

  const done = (remedy) => {
    if (remedy && key) setCached(key, remedy);
    refreshLists();
    router.back();
  };

  const submit = (body) => proGate(async () => {
    const remedy = id ? await remediesApi.update(id, body, todayISO())
      : (await remediesApi.create(body, todayISO())).remedies[0];
    if ('reminder' in body) syncSchedule();
    done(remedy);
  });

  const reset = () => proGate(async () => done(await remediesApi.update(id, { reset: true }, todayISO())));

  const remove = async () => {
    if (!(await confirm(t('remedies.remove'), t('remedies.removeConfirm', { title: data.title }),
      { ok: t('remedies.remove'), cancel: t('common.cancel'), destructive: true }))) return;
    await remediesApi.remove(id);
    refreshLists();
    syncSchedule();
    router.dismissTo(home); // the remedy's detail screen (if open) no longer exists
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: th.c.bg }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Screen tabs={false}>
        <Row style={{ justifyContent: 'space-between', paddingTop: 6, paddingBottom: 16 }}>
          <T v="screenTitle">{id ? t('remedies.editTitle') : t('remedies.newTitle')}</T>
          <Pressable onPress={() => router.back()} hitSlop={10} style={{ width: 30, height: 30, borderRadius: 15, backgroundColor: th.c.muted, alignItems: 'center', justifyContent: 'center' }}>
            <Text style={{ color: th.c.ink2 }}>✕</Text>
          </Pressable>
        </Row>
        {id && loading ? <Loading /> : null}
        {id && !data ? <ErrorView error={error} onRetry={refetch} /> : null}
        {!id || data ? (
          <RemedyForm
            key={data ? `${data.id}:${data.edited}` : 'new'}
            initial={data}
            onSubmit={submit}
            onReset={id ? reset : undefined}
            onRemove={id ? remove : undefined}
          />
        ) : null}
      </Screen>
    </KeyboardAvoidingView>
  );
}
