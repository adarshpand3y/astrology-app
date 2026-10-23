import { useLocalSearchParams } from 'expo-router';

import { RemedyEditScreen } from '../../../components/RemedyEditScreen';

export default function OnboardingEditRemedy() {
  const { id } = useLocalSearchParams();
  return <RemedyEditScreen id={id} home="/onboarding/remedies" />;
}
