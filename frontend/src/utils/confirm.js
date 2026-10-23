import { Alert, Platform } from 'react-native';

/** Yes/no confirmation that also works on web (react-native-web's Alert has no buttons). */
export function confirm(title, message, { ok, cancel, destructive } = {}) {
  if (Platform.OS === 'web') {
    return Promise.resolve(window.confirm(message ? `${title}\n\n${message}` : title));
  }
  return new Promise((resolve) => {
    Alert.alert(title, message, [
      { text: cancel || 'Cancel', style: 'cancel', onPress: () => resolve(false) },
      { text: ok || 'OK', style: destructive ? 'destructive' : 'default', onPress: () => resolve(true) },
    ], { cancelable: true, onDismiss: () => resolve(false) });
  });
}
