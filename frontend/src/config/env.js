import Constants from 'expo-constants';

const brand = require('../../brand.config');

function devApiUrl() {
  // In Expo Go the Metro host (e.g. "192.168.1.5:8081") is the developer's PC,
  // which is where `manage.py runserver 0.0.0.0:8000` is listening.
  const hostUri = Constants.expoConfig?.hostUri || Constants.expoGoConfig?.debuggerHost;
  const host = hostUri?.split(':')[0];
  return host ? `http://${host}:${brand.devApiPort}` : null;
}

function resolveApiUrl() {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) return fromEnv.replace(/\/+$/, '');
  if (__DEV__) return devApiUrl() || `http://localhost:${brand.devApiPort}`;
  return brand.apiUrl.replace(/\/+$/, '');
}

export const API_URL = resolveApiUrl();
export const API_BASE = `${API_URL}/api/v1`;
export const APP_ENV = Constants.expoConfig?.extra?.appEnv || (__DEV__ ? 'development' : 'production');
export { brand };
