import { Stack } from 'expo-router';

import { useTheme } from '../../theme';

// Signed-out users land here when a protected route is requested.
export const unstable_settings = { initialRouteName: 'sign-in' };

export default function AuthLayout() {
  const theme = useTheme();
  return (
    <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: theme.c.bg } }}>
      <Stack.Screen name="sign-in" />
    </Stack>
  );
}
