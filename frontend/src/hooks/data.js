// Query hooks. Keys include everything that changes a response (profile, place,
// date, language) so switching any of them fetches fresh data.
import {
  alertsApi, billingApi, dailyApi, journalApi, profilesApi, remediesApi, vedicApi,
} from '../api/endpoints';
import { useI18n } from '../i18n';
import { useAuth } from '../state/AuthContext';
import { todayISO } from '../utils/format';
import { useApi } from './useApi';

export function useAccount() {
  const { user } = useAuth();
  return {
    user,
    profileId: user?.active_profile_id || null,
    placeId: user?.current_place?.id || null,
  };
}

export function useHome(date) {
  const { profileId, placeId } = useAccount();
  const { lang } = useI18n();
  const d = date || todayISO();
  return useApi(profileId ? `home:${profileId}:${placeId}:${d}:${lang}` : null,
    () => dailyApi.home({ date: d }));
}

export function useTimeline(date) {
  const { placeId, profileId } = useAccount();
  const { lang } = useI18n();
  return useApi(`timeline:${profileId}:${placeId}:${date}:${lang}`, () => dailyApi.timeline({ date }));
}

export function usePanchang(date) {
  const { placeId, profileId } = useAccount();
  const { lang } = useI18n();
  return useApi(`panchang:${profileId}:${placeId}:${date}:${lang}`, () => dailyApi.panchang({ date }));
}

export const useProfiles = () => useApi('profiles', () => profilesApi.list());
export const useChart = (id) => useApi(id ? `p:${id}:chart` : null, () => vedicApi.chart(id));
/** One divisional chart, for when the cached chart doesn't include it (pass skip=true otherwise). */
export const useVarga = (id, code, skip) =>
  useApi(id && code && !skip ? `p:${id}:varga:${code}` : null, () => vedicApi.varga(id, code));
export const useDashaCurrent = (id) => useApi(id ? `p:${id}:dasha-current` : null, () => vedicApi.dashaCurrent(id));

/** Children of a dasha period ("" = the Mahadashas). */
export function useDashaLevel(id, path) {
  return useApi(id ? `p:${id}:dasha:${path}` : null,
    () => (path ? vedicApi.dashaDrill(id, path) : vedicApi.dashaTree(id)));
}

export function useStrength(id) {
  const { lang } = useI18n();
  return useApi(id ? `p:${id}:strength:${lang}` : null, () => vedicApi.strength(id));
}

export function useRemedies() {
  const { lang } = useI18n();
  const { profileId } = useAccount();
  return useApi(`remedies:${profileId}:${lang}`, () => remediesApi.list(todayISO()));
}

/** Done vs due per day for the last year (heatmap). */
export function useRemedyHistory() {
  const today = todayISO();
  return useApi(`remedy-history:${today}`, () => remediesApi.history(today));
}

export function useGoals() {
  const { lang } = useI18n();
  return useApi(`goals:${lang}`, () => remediesApi.goals());
}

export const useBilling = () => useApi('billing', () => billingApi.status());

export function useJournalDay(date) {
  const { lang } = useI18n();
  return useApi(`journal:${date}:${lang}`, () => journalApi.day(date));
}

export function useTrends(days = 30) {
  const { lang } = useI18n();
  const { profileId } = useAccount();
  const today = todayISO();
  return useApi(`trends:${profileId}:${days}:${today}:${lang}`, () => journalApi.trends(today, days));
}

export const useAlertPrefs = () => useApi('alert-prefs', () => alertsApi.prefs());

export function useSchedule() {
  const { lang } = useI18n();
  const { profileId, placeId } = useAccount();
  return useApi(`schedule:${profileId}:${placeId}:${lang}`, () => alertsApi.schedule(7));
}
