// Formatting helpers. Backend timestamps carry the place's UTC offset
// (e.g. "2026-10-19T06:29:30+05:30"); we show that wall-clock time as-is,
// independent of the phone's timezone.

export const MONTHS = {
  en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  hi: ['जन', 'फ़र', 'मार्च', 'अप्रै', 'मई', 'जून', 'जुला', 'अग', 'सितं', 'अक्टू', 'नवं', 'दिसं'],
};
const MONTHS_LONG = {
  en: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
  hi: ['जनवरी', 'फ़रवरी', 'मार्च', 'अप्रैल', 'मई', 'जून', 'जुलाई', 'अगस्त', 'सितंबर', 'अक्टूबर', 'नवंबर', 'दिसंबर'],
};
const DAYS = {
  en: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
  hi: ['रविवार', 'सोमवार', 'मंगलवार', 'बुधवार', 'गुरुवार', 'शुक्रवार', 'शनिवार'],
};
const DAYS_SHORT = {
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
  hi: ['रवि', 'सोम', 'मंगल', 'बुध', 'गुरु', 'शुक्र', 'शनि'],
};
/** Monday-first week letters for streak cells. */
export const DAY_LETTERS = { en: ['M', 'T', 'W', 'T', 'F', 'S', 'S'], hi: ['सो', 'मं', 'बु', 'गु', 'शु', 'श', 'र'] };

const UNITS = { en: { y: 'y', m: 'm', d: 'd', h: 'h', min: 'm' }, hi: { y: 'व', m: 'मा', d: 'दि', h: 'घं', min: 'मि' } };

const ISO_RE = /^(-?\d{4})-(\d{2})-(\d{2})(?:T(\d{2}):(\d{2})(?::(\d{2}))?)?/;
const pad = (n) => String(n).padStart(2, '0');

export function parts(iso) {
  const m = ISO_RE.exec(iso || '');
  if (!m) return null;
  const p = { y: +m[1], mo: +m[2], d: +m[3], h: m[4] ? +m[4] : 0, mi: m[5] ? +m[5] : 0 };
  p.wd = new Date(Date.UTC(p.y, p.mo - 1, p.d)).getUTCDay();
  return p;
}

/** "9:07" (en, 12h) / "09:07" (hi, 24h); withSuffix adds AM/PM. */
export function clock(iso, lang = 'en', withSuffix = false) {
  const p = parts(iso);
  if (!p) return '—';
  if (lang === 'hi') return `${pad(p.h)}:${pad(p.mi)}`;
  const h12 = p.h % 12 || 12;
  return `${h12}:${pad(p.mi)}${withSuffix ? (p.h < 12 ? ' AM' : ' PM') : ''}`;
}

/** "6:02–7:39 AM" or "11:58 AM–12:49 PM". */
export function range(startIso, endIso, lang = 'en') {
  if (!endIso) return clock(startIso, lang, true);
  if (lang === 'hi') return `${clock(startIso, lang)}–${clock(endIso, lang)}`;
  const a = parts(startIso);
  const b = parts(endIso);
  const same = (a.h < 12) === (b.h < 12);
  return same ? `${clock(startIso)}–${clock(endIso, 'en', true)}` : `${clock(startIso, 'en', true)}–${clock(endIso, 'en', true)}`;
}

/** "Saturday · 19 July" */
export function dateLine(iso, lang = 'en') {
  const p = parts(iso);
  if (!p) return '';
  return `${DAYS[lang][p.wd]} · ${p.d} ${MONTHS_LONG[lang][p.mo - 1]}`;
}

/** "Sat 19 Jul" */
export function shortDate(iso, lang = 'en', comma = false) {
  const p = parts(iso);
  if (!p) return '';
  return `${DAYS_SHORT[lang][p.wd]}${comma ? ',' : ''} ${p.d} ${MONTHS[lang][p.mo - 1]}`;
}

/** "14 Aug 1994" */
export function fullDate(iso, lang = 'en') {
  const p = parts(iso);
  if (!p) return '—';
  return `${p.d} ${MONTHS[lang][p.mo - 1]} ${p.y}`;
}

/** Day + time for ranked windows: { day: "Tue 22", time: "2:20 PM" } */
export function dayAndTime(iso, lang = 'en') {
  const p = parts(iso);
  return { day: `${DAYS_SHORT[lang][p.wd]} ${p.d}`, time: clock(iso, lang, true) };
}

/** Dasha range formats by level (0 = Mahadasha): year · Mon YYYY · D Mon 'YY · D Mon, HH:MM */
export function dashaDate(iso, level, lang = 'en') {
  const p = parts(iso);
  if (!p) return '';
  if (level === 0) return String(p.y);
  if (level === 1) return `${MONTHS[lang][p.mo - 1]} ${p.y}`;
  if (level < 4) return `${p.d} ${MONTHS[lang][p.mo - 1]} ’${String(p.y).slice(2)}`;
  return `${p.d} ${MONTHS[lang][p.mo - 1]}, ${pad(p.h)}:${pad(p.mi)}`;
}

/** Human duration like the design: "1y 4m", "3m 12d", "5d 6h", "4h 20m". */
export function duration(ms, lang = 'en') {
  const u = UNITS[lang] || UNITS.en;
  const DAY = 86400000;
  const YR = 365.25 * DAY;
  const y = ms / YR;
  if (y >= 1) {
    const m = Math.floor((y % 1) * 12);
    return `${Math.floor(y)}${u.y}${m ? ` ${m}${u.m}` : ''}`;
  }
  const d = ms / DAY;
  if (d >= 60) return `${Math.floor(d / 30.44)}${u.m} ${Math.round(d % 30.44)}${u.d}`;
  if (d >= 1) {
    const h = Math.round((d % 1) * 24);
    return `${Math.floor(d)}${u.d}${h ? ` ${h}${u.h}` : ''}`;
  }
  const h = ms / 3600000;
  return `${Math.floor(h)}${u.h} ${Math.round((h % 1) * 60)}${u.min}`;
}

export const num = (v, digits = 2) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(digits));

export function progress(startIso, endIso, now = Date.now()) {
  const s = Date.parse(startIso);
  const e = Date.parse(endIso);
  if (!s || !e || e <= s) return 0;
  return Math.min(1, Math.max(0, (now - s) / (e - s)));
}

// --- values sent to the API (from the phone's local Date components) ---------------
export const toApiDate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
export const toApiTime = (d) => `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
export const todayISO = () => toApiDate(new Date());

export function addDays(isoDate, n) {
  const [y, m, d] = isoDate.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + n));
  return `${dt.getUTCFullYear()}-${pad(dt.getUTCMonth() + 1)}-${pad(dt.getUTCDate())}`;
}

export function fromApiDateTime(date, time) {
  const [y, mo, d] = (date || '2000-01-01').split('-').map(Number);
  const [h, mi, s] = (time || '12:00:00').split(':').map(Number);
  return new Date(y, mo - 1, d, h || 0, mi || 0, s || 0);
}

export function displayDate(d, lang = 'en') {
  return `${d.getDate()} ${MONTHS[lang][d.getMonth()]} ${d.getFullYear()}`;
}

export function displayTime(d, lang = 'en') {
  if (lang === 'hi') return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  return `${d.getHours() % 12 || 12}:${pad(d.getMinutes())} ${d.getHours() < 12 ? 'AM' : 'PM'}`;
}

export function initials(name) {
  return (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join('');
}

/** User-facing message for an ApiError. */
export function errorMessage(err, t) {
  if (!err) return '';
  if (err.code === 'network_error') return t('common.networkError');
  if (err.code === 'offline') return t('offline.readOnly');
  if (err.code === 'timeout') return t('common.timeoutError');
  return err.message || t('common.unknownError');
}

/** Field errors from a DRF validation envelope: { field: "first message" } (nested one level). */
export function fieldErrors(err) {
  const details = err?.details;
  if (!details || typeof details !== 'object' || Array.isArray(details)) return {};
  const out = {};
  Object.entries(details).forEach(([k, v]) => {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      Object.entries(v).forEach(([k2, v2]) => { out[`${k}.${k2}`] = Array.isArray(v2) ? String(v2[0]) : String(v2); });
    } else {
      out[k] = Array.isArray(v) ? String(v[0]) : String(v);
    }
  });
  return out;
}
