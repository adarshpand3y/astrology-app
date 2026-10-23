// One function per backend endpoint (see backend/README.md).
import { api } from './client';

const post = (path, body, opts) => api(path, { method: 'POST', body, ...opts });

export const authApi = {
  register: (data) => post('/auth/register/', data, { auth: false }),
  verifyEmail: (email, code) => post('/auth/verify-email/', { email, code }, { auth: false }),
  resendVerification: (email) => post('/auth/resend-verification/', { email }, { auth: false }),
  login: (email, password) => post('/auth/login/', { email, password }, { auth: false }),
  logout: (refresh) => post('/auth/logout/', { refresh }),
  me: () => api('/auth/me/'),
  updateMe: (data) => api('/auth/me/', { method: 'PATCH', body: data }),
  deleteMe: (password) => api('/auth/me/', { method: 'DELETE', body: { password } }),
  changePassword: (oldPassword, newPassword) =>
    post('/auth/change-password/', { old_password: oldPassword, new_password: newPassword }),
  requestReset: (email) => post('/auth/password-reset/request/', { email }, { auth: false }),
  confirmReset: (email, code, newPassword) =>
    post('/auth/password-reset/confirm/', { email, code, new_password: newPassword }, { auth: false }),
};

export const placesApi = {
  search: (q) => api('/places/search/', { query: { q } }),
};

export const profilesApi = {
  list: () => api('/profiles/', { query: { page_size: 100 } }),
  get: (id) => api(`/profiles/${id}/`),
  create: (data) => post('/profiles/', data),
  update: (id, data) => api(`/profiles/${id}/`, { method: 'PATCH', body: data }),
  remove: (id) => api(`/profiles/${id}/`, { method: 'DELETE' }),
};

export const vedicApi = {
  chart: (id) => api(`/profiles/${id}/chart/`, { timeout: 40000 }),
  varga: (id, code) => api(`/profiles/${id}/vargas/${code}/`, { timeout: 40000 }),
  dashaTree: (id) => api(`/profiles/${id}/dashas/`, { query: { depth: 1 } }),
  dashaDrill: (id, path) => api(`/profiles/${id}/dashas/drill/`, { query: { path } }),
  dashaCurrent: (id) => api(`/profiles/${id}/dashas/current/`),
  strength: (id) => api(`/profiles/${id}/strength-report/`, { timeout: 40000 }),
};

export const dailyApi = {
  home: (query) => api('/daily/home/', { query }),
  timeline: (query) => api('/daily/timeline/', { query }),
  panchang: (query) => api('/daily/panchang/', { query }),
  decision: (activity, range) => post('/daily/decision/', { activity, range }, { timeout: 40000 }),
};

export const remediesApi = {
  list: (today) => api('/remedies/', { query: { today } }),
  get: (id, today) => api(`/remedies/${id}/`, { query: { today } }),
  add: (planet) => post('/remedies/', { planet }),
  /** Custom remedy: { title, text?, how?, target?, weekdays? } (Pro). */
  create: (body, today) => post('/remedies/', body, { query: { today } }),
  /** Edit (Pro): { title, text, how, target, weekdays, reminder } or { reset: true }. */
  update: (id, patch, today) => api(`/remedies/${id}/`, { method: 'PATCH', body: patch, query: { today } }),
  remove: (id) => api(`/remedies/${id}/`, { method: 'DELETE' }),
  progress: (id, body) => post(`/remedies/${id}/progress/`, body),
  goals: () => api('/remedies/goals/'),
  setGoals: (goals, today) => api('/remedies/goals/', { method: 'PUT', body: { goals }, query: { today } }),
  history: (today, days = 365) => api('/remedies/history/', { query: { today, days } }),
};

export const journalApi = {
  day: (date) => api(`/journal/${date}/`),
  save: (date, body, today) => api(`/journal/${date}/`, { method: 'PUT', body, query: { today } }),
  /** Mood + remedies done/due per day for the last `days` (7–90), with insights. */
  trends: (today, days = 14) => api('/journal/trends/', { query: { today, days } }),
};

export const alertsApi = {
  prefs: () => api('/alerts/prefs/'),
  update: (patch) => api('/alerts/prefs/', { method: 'PATCH', body: patch }),
  schedule: (days = 7) => api('/alerts/schedule/', { query: { days } }),
};

export const billingApi = {
  status: () => api('/billing/'),
  startTrial: () => post('/billing/trial/'),
};
