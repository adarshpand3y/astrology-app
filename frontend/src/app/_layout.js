import { HankenGrotesk_400Regular, HankenGrotesk_500Medium, HankenGrotesk_600SemiBold, HankenGrotesk_700Bold } from '@expo-google-fonts/hanken-grotesk';
import { Newsreader_400Regular, Newsreader_500Medium, Newsreader_600SemiBold } from '@expo-google-fonts/newsreader';
import { SplineSansMono_400Regular, SplineSansMono_500Medium, SplineSansMono_600SemiBold } from '@expo-google-fonts/spline-sans-mono';
import { useFonts } from 'expo-font';
import { Stack } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { setApiLanguage } from '../api/client';
import { useI18n } from '../i18n';
import { setupNotifications, syncSchedule } from '../notifications';
import { AuthProvider, useAuth } from '../state/AuthContext';
import { PrefsProvider, usePrefs } from '../state/PrefsContext';
import { useTheme } from '../theme';

SplashScreen.preventAutoHideAsync().catch(() => {});

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <PrefsProvider>
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </PrefsProvider>
    </SafeAreaProvider>
  );
}

function RootNavigator() {
  const { status, user } = useAuth();
  const { ready, lang } = usePrefs();
  const { t } = useI18n();
  const theme = useTheme();
  const [fontsLoaded, fontError] = useFonts({
    Newsreader_400Regular, Newsreader_500Medium, Newsreader_600SemiBold,
    HankenGrotesk_400Regular, HankenGrotesk_500Medium, HankenGrotesk_600SemiBold, HankenGrotesk_700Bold,
    SplineSansMono_400Regular, SplineSansMono_500Medium, SplineSansMono_600SemiBold,
  });
  const booting = status === 'loading' || !ready || (!fontsLoaded && !fontError);

  useEffect(() => { setApiLanguage(lang); }, [lang]);
  useEffect(() => {
    if (!booting) SplashScreen.hideAsync().catch(() => {});
  }, [booting]);

  // Ask for notification permission as soon as the app opens (before sign-in), then offer
  // on-time ("Alarms & reminders") delivery once. Signed-in users get their alerts scheduled
  // straight away; others when they reach the tabs after signing in.
  const asked = useRef(false);
  useEffect(() => {
    if (booting || asked.current) return;
    asked.current = true;
    setupNotifications({
      title: t('alerts.exactTitle'), message: t('alerts.exactPrompt'),
      later: t('alerts.exactLater'), allow: t('alerts.exactAllow'),
    }).then((ok) => { if (ok && status === 'signedIn') syncSchedule(); });
  }, [booting, status, t]);

  if (booting) return null;
  const signedIn = status === 'signedIn';
  // New accounts finish onboarding (birth profile, then goals) before reaching the app.
  // `user` can be null after an offline launch; let those users into the app.
  const onboarding = signedIn && !!user?.needs_onboarding;

  return (
    <>
      <StatusBar style={theme.dark ? 'light' : 'dark'} />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: theme.c.bg } }}>
        <Stack.Protected guard={signedIn && !onboarding}>
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="paywall" options={{ presentation: 'modal' }} />
          <Stack.Screen name="goals" options={{ presentation: 'modal' }} />
          <Stack.Screen name="profile/new" options={{ presentation: 'modal' }} />
          <Stack.Screen name="profile/edit/[id]" options={{ presentation: 'modal' }} />
        </Stack.Protected>
        <Stack.Protected guard={onboarding}>
          <Stack.Screen name="onboarding" />
        </Stack.Protected>
        <Stack.Protected guard={!signedIn}>
          <Stack.Screen name="(auth)" />
        </Stack.Protected>
      </Stack>
    </>
  );
}
