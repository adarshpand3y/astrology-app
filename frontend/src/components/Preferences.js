import { Text, View } from 'react-native';

import { brand } from '../config/env';
import { LANGUAGE_NAMES, LANGUAGES, useI18n } from '../i18n';
import { usePrefs } from '../state/PrefsContext';
import { useTheme } from '../theme';
import { clock } from '../utils/format';
import { Row, Seg, Switch, T } from './ui';

export const ALERT_FIELDS = ['dasha', 'transit', 'rahu', 'sade_sati', 'daily', 'remedies', 'periods', 'periods_night'];

/** Theme, language and chart style; stored on this phone (shared by Settings and onboarding). */
export function AppearanceSettings() {
  const { t } = useI18n();
  const { prefs, update } = usePrefs();
  return (
    <>
      <T v="label" style={{ marginBottom: 8 }}>{t('settings.theme')}</T>
      <Seg value={prefs.themeMode} onChange={(v) => update({ themeMode: v })}
        options={['system', 'light', 'dark'].map((v) => ({ value: v, label: t(`settings.${v}`) }))} />
      {LANGUAGES.length > 1 ? (
        <>
          <T v="label" style={{ marginTop: 16, marginBottom: 8 }}>{t('settings.language')}</T>
          <Seg value={prefs.language} onChange={(v) => update({ language: v })}
            options={[{ value: 'system', label: t('settings.system') }, ...LANGUAGES.map((l) => ({ value: l, label: LANGUAGE_NAMES[l] }))]} />
        </>
      ) : null}
      {brand.features.southIndianChart ? (
        <>
          <T v="label" style={{ marginTop: 16, marginBottom: 8 }}>{t('settings.chartStyle')}</T>
          <Seg value={prefs.chartStyle} onChange={(v) => update({ chartStyle: v })}
            options={[{ value: 'north', label: t('settings.north') }, { value: 'south', label: t('settings.south') }]} />
        </>
      ) : null}
    </>
  );
}

/** One switch per alert kind. `prefs` is the server's alert-prefs payload; Pro fields carry a badge. */
export function AlertToggles({ prefs: p, onToggle, fields = ALERT_FIELDS }) {
  const th = useTheme();
  const { t, lang } = useI18n();

  const sub = (field) => {
    if (field === 'rahu') return t('alerts.rahuSub', { n: p.rahu_lead_minutes });
    if (field === 'daily' || field === 'remedies') {
      const [h, m] = (field === 'daily' ? p.daily_time : p.remedy_time).split(':');
      return t(`alerts.${field}Sub`, { t: clock(`2000-01-01T${h}:${m}`, lang, true) });
    }
    return t(`alerts.${field}Sub`);
  };

  return (
    <View style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair, borderRadius: 18, overflow: 'hidden' }}>
      {fields.map((f, i) => (
        <Row key={f} gap={13} style={{ paddingVertical: 14, paddingHorizontal: 16, borderTopWidth: i ? 1 : 0, borderTopColor: th.c.hair }}>
          <View style={{ flex: 1 }}>
            <T weight={600} style={{ fontSize: 14 }}>
              {t(`alerts.${f}`)}{p.pro_fields.includes(f) && !p.is_pro ? <Text style={{ color: th.c.accent, fontSize: 11 }}>  ◆ {t('common.pro')}</Text> : null}
            </T>
            <T v="caption" style={{ marginTop: 1 }}>{sub(f)}</T>
          </View>
          <Switch value={!!p[f]} onChange={() => onToggle(f)} />
        </Row>
      ))}
    </View>
  );
}
