import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, TextInput, View } from 'react-native';
import Svg, { Circle, Path } from 'react-native-svg';

import { placesApi } from '../api/endpoints';
import { useI18n } from '../i18n';
import { ERROR, useTheme } from '../theme';
import { errorMessage } from '../utils/format';
import { T } from './ui';

export const placeCity = (p) => (p?.label || '').split(',')[0].trim();
export const placeRegion = (p) => (p?.label || '').split(',').slice(1).map((s) => s.trim()).filter(Boolean).join(', ');

function Icon({ kind, color }) {
  return (
    <Svg width={15} height={15} viewBox="0 0 16 16" fill="none">
      {kind === 'pin' ? (
        <>
          <Path d="M8 1.5c2.8 0 5 2.2 5 5 0 3.5-5 8-5 8s-5-4.5-5-8c0-2.8 2.2-5 5-5z" stroke={color} strokeWidth={1.4} />
          <Circle cx={8} cy={6.5} r={1.8} stroke={color} strokeWidth={1.4} />
        </>
      ) : (
        <>
          <Circle cx={8} cy={8} r={5.5} stroke={color} strokeWidth={1.4} />
          <Circle cx={8} cy={8} r={1.8} fill={color} />
        </>
      )}
    </Svg>
  );
}

/**
 * Restricted location picker: free text is never accepted. Focusing clears the
 * box to a search; picking a row commits it; blurring without a pick reverts.
 */
export function LocationPicker({ label, hint, icon = 'pin', value, onChange, error }) {
  const th = useTheme();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [results, setResults] = useState([]);
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState(null);
  const seq = useRef(0);
  const input = useRef(null);
  const picking = useRef(false);

  useEffect(() => {
    const query = q.trim();
    if (!open || query.length < 2) return undefined;
    const id = ++seq.current;
    const timer = setTimeout(async () => {
      setBusy(true);
      try {
        const r = await placesApi.search(query);
        if (id === seq.current) { setResults(r.results.slice(0, 8)); setFailure(null); }
      } catch (e) {
        if (id === seq.current) { setResults([]); setFailure(e); }
      } finally {
        if (id === seq.current) setBusy(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [q, open]);

  const searching = open && q.trim().length >= 2;
  const shown = searching ? results : [];

  const pick = (p) => {
    picking.current = false;
    onChange(p);
    setOpen(false);
    setQ('');
    input.current?.blur();
  };

  return (
    <View>
      {label ? (
        <T v="label" style={{ marginBottom: 6 }}>
          {label}{hint ? <T v="label" style={{ color: th.c.ink3, fontWeight: '400' }}>{hint}</T> : null}
        </T>
      ) : null}
      <View style={{
        backgroundColor: th.c.surface, borderWidth: 1, borderRadius: 13, padding: 13, flexDirection: 'row', alignItems: 'center', gap: 9,
        borderColor: error ? ERROR : open ? th.c.accent : th.c.hair2,
      }}>
        <Icon kind={icon} color={th.c.accent} />
        <TextInput
          ref={input}
          value={open ? q : placeCity(value)}
          placeholder={t('auth.searchCity')}
          placeholderTextColor={th.c.ink3}
          onFocus={() => { setOpen(true); setQ(''); setResults([]); }}
          onBlur={() => { if (!picking.current) { setOpen(false); setQ(''); } }}
          onChangeText={setQ}
          autoCorrect={false}
          style={[th.font.ui(400), { flex: 1, fontSize: 15, color: th.c.ink, padding: 0 }]}
        />
        {!open && value ? <T v="tiny" numberOfLines={1} style={{ maxWidth: '45%' }}>{placeRegion(value)}</T> : null}
      </View>
      {open ? (
        <>
          {searching ? (
            <View style={[{
              marginTop: 6, maxHeight: 212, backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair,
              borderRadius: 13, overflow: 'hidden',
            }, th.shadow('card')]}>
              <ScrollView nestedScrollEnabled keyboardShouldPersistTaps="always">
                {busy && !shown.length ? <ActivityIndicator style={{ padding: 13 }} color={th.c.accent} /> : null}
                {!busy && !shown.length && failure ? <T v="small" style={{ padding: 13, color: ERROR }}>{errorMessage(failure, t)}</T> : null}
                {!busy && !shown.length && !failure ? <T v="small" style={{ padding: 13, color: th.c.ink3 }}>{t('auth.noMatch', { q: q.trim() })}</T> : null}
                {shown.map((p, i) => (
                  <Pressable
                    key={p.id}
                    onPressIn={() => { picking.current = true; }}
                    onPress={() => pick(p)}
                    style={({ pressed }) => ({
                      flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10,
                      paddingVertical: 11, paddingHorizontal: 13,
                      borderBottomWidth: i < shown.length - 1 ? 1 : 0, borderBottomColor: th.c.hair,
                      backgroundColor: pressed || p.id === value?.id ? th.soft(0.09) : 'transparent',
                    })}
                  >
                    <T style={{ fontSize: 14 }}>{placeCity(p)}</T>
                    <T v="tiny" numberOfLines={1} style={{ fontSize: 12, flexShrink: 1, textAlign: 'right' }}>{placeRegion(p)}</T>
                  </Pressable>
                ))}
              </ScrollView>
            </View>
          ) : null}
          <T v="tiny" style={{ marginTop: 6 }}>{t('auth.pickHint')}</T>
        </>
      ) : null}
      {error && !open ? <T v="caption" style={{ color: ERROR, marginTop: 6 }}>{error}</T> : null}
    </View>
  );
}
