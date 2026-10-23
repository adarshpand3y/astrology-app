import { useLocalSearchParams } from 'expo-router';

import { RemedyEditScreen } from '../../../../components/RemedyEditScreen';

export default function EditRemedy() {
  const { id } = useLocalSearchParams();
  return <RemedyEditScreen id={id} />;
}
