import { useState } from 'react';
import { View } from 'react-native';

import { useI18n } from '../i18n';
import { displayDate, displayTime, MONTHS } from '../utils/format';
import { Button, FieldBox, Sheet, T } from './ui';
import { Wheel, WheelGroup } from './WheelPicker';

const MIN_YEAR = 1850; // backend ephemeris range starts here
const MAX_YEAR = new Date().getFullYear();
const YEARS = Array.from({ length: MAX_YEAR - MIN_YEAR + 1 }, (_, i) => String(MIN_YEAR + i));
const pad = (n) => String(n).padStart(2, '0');
const MINUTES = Array.from({ length: 60 }, (_, i) => pad(i));
const HOURS_12 = Array.from({ length: 12 }, (_, i) => String(i + 1));
const HOURS_24 = Array.from({ length: 24 }, (_, i) => pad(i));

const daysIn = (y, m) => new Date(y, m + 1, 0).getDate();

// Where the wheels start when nothing has been chosen yet.
const seed = (mode) => (mode === 'date' ? new Date(2000, 0, 1) : new Date(2000, 0, 1, 12, 0));

function DateWheels({ value, onChange, lang }) {
  const y = value.getFullYear();
  const m = value.getMonth();
  const n = daysIn(y, m);
  const days = Array.from({ length: n }, (_, i) => String(i + 1));
  // Changing month/year keeps the day where possible, else clamps (31 Jan -> 28 Feb).
  const set = (yy, mm, dd) => onChange(new Date(yy, mm, Math.min(dd, daysIn(yy, mm))));
  return (
    <WheelGroup>
      <Wheel flex={0.8} items={days} index={Math.min(value.getDate(), n) - 1} onChange={(i) => set(y, m, i + 1)} />
      <Wheel flex={1.3} items={MONTHS[lang]} index={m} onChange={(i) => set(y, i, value.getDate())} />
      <Wheel flex={1} items={YEARS} index={clamp(y - MIN_YEAR, 0, YEARS.length - 1)}
        onChange={(i) => set(MIN_YEAR + i, m, value.getDate())} />
    </WheelGroup>
  );
}

function TimeWheels({ value, onChange, h24 }) {
  const h = value.getHours();
  const mi = value.getMinutes();
  const set = (hh, mm) => { const d = new Date(value); d.setHours(hh, mm, 0, 0); onChange(d); };
  if (h24) {
    return (
      <WheelGroup>
        <Wheel items={HOURS_24} index={h} onChange={(i) => set(i, mi)} />
        <Wheel items={MINUTES} index={mi} onChange={(i) => set(h, i)} />
      </WheelGroup>
    );
  }
  const pm = h >= 12;
  return (
    <WheelGroup>
      <Wheel items={HOURS_12} index={(h % 12 || 12) - 1} onChange={(i) => set(((i + 1) % 12) + (pm ? 12 : 0), mi)} />
      <Wheel items={MINUTES} index={mi} onChange={(i) => set(h, i)} />
      <Wheel items={['AM', 'PM']} index={pm ? 1 : 0} onChange={(i) => set((h % 12) + (i ? 12 : 0), mi)} />
    </WheelGroup>
  );
}

function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

/**
 * Tappable field that opens a bottom sheet of scroll wheels.
 * mode: "date" | "time". `value` may be null (placeholder until picked).
 * `display` overrides the shown text (e.g. "Unknown").
 */
export function DateTimeField({ label, value, onChange, mode = 'date', disabled, display, muted, error, style }) {
  const { t, lang } = useI18n();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(() => value || seed(mode));
  const h24 = lang === 'hi';

  const show = () => {
    if (disabled) return;
    setDraft(value || seed(mode));
    setOpen(true);
  };

  const text = display || (value ? (mode === 'date' ? displayDate(value, lang) : displayTime(value, lang)) : '');
  return (
    <View style={style}>
      <FieldBox label={label} value={text} placeholder={t(mode === 'date' ? 'auth.datePh' : 'auth.timePh')}
        onPress={show} muted={muted || disabled} error={disabled ? null : error} />
      <Sheet visible={open} onClose={() => setOpen(false)}>
        {label ? <T v="eyebrow" style={{ textAlign: 'center', marginBottom: 6 }}>{label}</T> : null}
        <T v="cardTitle" style={{ textAlign: 'center', fontSize: 20, marginBottom: 14 }}>
          {mode === 'date' ? displayDate(draft, lang) : displayTime(draft, lang)}
        </T>
        {mode === 'date'
          ? <DateWheels value={draft} onChange={setDraft} lang={lang} />
          : <TimeWheels value={draft} onChange={setDraft} h24={h24} />}
        <Button title={t('common.done')} onPress={() => { onChange(draft); setOpen(false); }} style={{ marginTop: 18 }} />
      </Sheet>
    </View>
  );
}
