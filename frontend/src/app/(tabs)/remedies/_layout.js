import { Stack } from 'expo-router';

import { useTheme } from '../../../theme';

// A screen opened from another tab (e.g. Home -> Dasha) sits on top of the tab's main page,
// so Back returns to that page and the tab doesn't reopen on the inner screen.
export const unstable_settings = { initialRouteName: 'index' };

export default function TabStack() {
  const theme = useTheme();
  return <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: theme.c.bg } }} />;
}
