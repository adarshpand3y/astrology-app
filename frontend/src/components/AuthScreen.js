import { KeyboardAvoidingView, Platform, ScrollView, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useTheme } from '../theme';
import { FadeIn, Orb, T } from './ui';

export const EMAIL_RE = /^\S+@\S+\.\S+$/;

/** Login / sign-up / onboarding canvas: 26px gutters, breathing orb, centred title, optional header above. */
export function AuthScreen({ title, sub, children, orbTop = 44, showOrb = true, header }) {
  const th = useTheme();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: th.c.bg }}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={{ flexGrow: 1, paddingHorizontal: 26, paddingTop: 22, paddingBottom: 34 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <FadeIn style={{ flexGrow: 1 }}>
            {header}
            <View style={{ alignItems: 'center', gap: 16, paddingTop: showOrb ? orbTop : 0, paddingBottom: 26 }}>
              {showOrb ? <Orb /> : null}
              <View style={{ alignItems: 'center' }}>
                <T v="heroTitle" style={{ textAlign: 'center' }}>{title}</T>
                {sub ? <T v="small" style={{ fontSize: 13.5, lineHeight: 20, marginTop: 5, textAlign: 'center', maxWidth: 270 }}>{sub}</T> : null}
              </View>
            </View>
            {children}
          </FadeIn>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
