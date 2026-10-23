import { useRouter } from 'expo-router';
import { Pressable, Text } from 'react-native';

import { brand } from '../config/env';
import { useI18n } from '../i18n';
import { useTheme } from '../theme';
import { addDays, shortDate, todayISO } from '../utils/format';
import { Row, Seg } from './ui';

/** Switch between the three Timeline-tab screens. */
export function TimelineNav({ current }) {
  const { t } = useI18n();
  const router = useRouter();
  const options = [
    { value: 'index', label: t('timeline.segTimeline') },
    brand.features.decisionAssistant && { value: 'decision', label: t('timeline.segDecision') },
    brand.features.panchang && { value: 'panchang', label: t('timeline.segPanchang') },
  ].filter(Boolean);
  return (
    <Seg
      options={options}
      value={current}
      onChange={(v) => v !== current && router.replace(v === 'index' ? '/timeline' : `/timeline/${v}`)}
      style={{ marginBottom: 16 }}
    />
  );
}

/** The design's "‹ Today ›" date pager. */
export function DatePager({ date, onChange }) {
  const th = useTheme();
  const { t, lang } = useI18n();
  const label = date === todayISO() ? t('common.today') : shortDate(date, lang);
  const arrow = (dir) => (
    <Pressable hitSlop={10} onPress={() => onChange(addDays(date, dir))}>
      <Text style={{ fontSize: 15, color: th.c.ink2, paddingHorizontal: 2 }}>{dir < 0 ? '‹' : '›'}</Text>
    </Pressable>
  );
  return (
    <Row gap={10} style={{ backgroundColor: th.c.surface, borderWidth: 1, borderColor: th.c.hair2, borderRadius: 11, paddingVertical: 6, paddingHorizontal: 11 }}>
      {arrow(-1)}
      <Pressable onPress={() => onChange(todayISO())}>
        <Text style={[th.font.ui(600), { fontSize: 12.5, color: th.c.ink, minWidth: 64, textAlign: 'center' }]}>{label}</Text>
      </Pressable>
      {arrow(1)}
    </Row>
  );
}
