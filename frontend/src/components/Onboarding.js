import { Pressable, View } from 'react-native';

import { useI18n } from '../i18n';
import { useAuth } from '../state/AuthContext';
import { useTheme } from '../theme';
import { AuthScreen } from './AuthScreen';
import { Row, T } from './ui';

/** Onboarding step canvas: "Step n of 3" progress bar, sign-out escape hatch, then the auth layout. */
export function OnboardingScreen({ step, title, sub, children }) {
  const th = useTheme();
  const { t } = useI18n();
  const { signOut } = useAuth();
  const header = (
    <View style={{ gap: 10, marginBottom: step === 1 ? 0 : 24 }}>
      <Row style={{ justifyContent: 'space-between' }}>
        <T v="eyebrow">{t('onboarding.step', { n: step })}</T>
        <Pressable onPress={signOut} hitSlop={8}>
          <T v="tiny" style={{ color: th.c.ink3 }}>{t('onboarding.signOut')}</T>
        </Pressable>
      </Row>
      <Row gap={6}>
        {[1, 2, 3].map((n) => (
          <View key={n} style={{ flex: 1, height: 4, borderRadius: 2, backgroundColor: n <= step ? th.c.accent : th.c.track }} />
        ))}
      </Row>
    </View>
  );
  return <AuthScreen header={header} title={title} sub={sub} orbTop={22} showOrb={step === 1}>{children}</AuthScreen>;
}
