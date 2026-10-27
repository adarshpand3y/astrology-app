// Connectivity. While offline the app is read-only: screens show the saved results
// (hooks/useApi persists them) and every change to the server is refused up front.
import NetInfo from '@react-native-community/netinfo';
import { useSyncExternalStore } from 'react';
import { Alert } from 'react-native';

let online = true; // optimistic until NetInfo reports, so a normal launch never flashes "offline"
const listeners = new Set();

// isInternetReachable is null while NetInfo is still checking; only a definite false counts.
const isOnline = (s) => s.isConnected !== false && s.isInternetReachable !== false;

NetInfo.addEventListener((s) => {
  const next = isOnline(s);
  if (next === online) return;
  online = next;
  listeners.forEach((l) => l(online));
});

export const network = {
  isOnline: () => online,
  /** Current state straight from the OS (used at launch, before the listener has fired). */
  check: () => NetInfo.fetch().then((s) => { online = isOnline(s); return online; }).catch(() => online),
  subscribe(cb) {
    listeners.add(cb);
    return () => listeners.delete(cb);
  },
};

export function useOnline() {
  return useSyncExternalStore(network.subscribe, network.isOnline);
}

/** Guard for actions that change data: explains and returns false while offline. */
export function requireOnline(t) {
  if (online) return true;
  Alert.alert(t('offline.title'), t('offline.readOnly'));
  return false;
}
