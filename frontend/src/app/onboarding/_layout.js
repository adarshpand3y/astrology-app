import { Stack } from 'expo-router';

import { useTheme } from '../../theme';

export default function OnboardingLayout() {
  const theme = useTheme();
  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: theme.c.bg } }}>
      <Stack.Screen name="index" />
      <Stack.Screen name="edit/[id]" options={{ presentation: 'modal' }} />
    </Stack>
  );
}
