import { Redirect } from 'expo-router';

import { useAuth } from '../../state/AuthContext';

/** Resume onboarding where the account left off: birth details first, then goals. */
export default function OnboardingStart() {
  const { user } = useAuth();
  return <Redirect href={user?.active_profile_id ? '/onboarding/goals' : '/onboarding/profile'} />;
}
