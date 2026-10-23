import { Pressable, Text, View } from 'react-native';

import { useI18n } from '../i18n';
import { useTheme } from '../theme';
import { RemedyIcon } from './Icons';
import { T } from './ui';

/**
 * Compact remedy row: glyph; title, the goal it serves, then cadence · graha. `right` holds the
 * actions — edit + done on the Remedies page, edit/remove in onboarding.
 */
export function RemedyCard({ remedy: r, onPress, right }) {
  const th = useTheme();
  const { t } = useI18n();
  const details = [r.cadence, r.planet_name, r.edited && t('remedies.edited')].filter(Boolean).join(' · ');
  return (
    <View style={{
      flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: th.c.surface,
      borderWidth: 1, borderColor: th.c.hair, borderRadius: 16, paddingVertical: 11, paddingLeft: 13, paddingRight: 10,
    }}>
      <Pressable onPress={onPress} disabled={!onPress} style={{ flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
        <View style={{ width: 36, height: 36, borderRadius: 11, backgroundColor: th.soft(0.15), alignItems: 'center', justifyContent: 'center' }}>
          <RemedyIcon kind={r.kind} size={20} color={th.c.accent} />
        </View>
        <View style={{ flex: 1, minWidth: 0 }}>
          <T weight={600} style={{ fontSize: 14.5 }} numberOfLines={2}>{r.title}</T>
          {r.goal_short ? (
            <View style={{
              alignSelf: 'flex-start', marginTop: 4, paddingVertical: 2, paddingHorizontal: 8, borderRadius: 20,
              backgroundColor: th.soft(0.12),
            }}>
              <Text numberOfLines={1} style={[th.font.ui(600), { fontSize: 10.5, color: th.c.accentDark }]}>{r.goal_short}</Text>
            </View>
          ) : null}
          <T v="caption" style={{ marginTop: 4 }} numberOfLines={1}>{details}</T>
        </View>
      </Pressable>
      {right}
    </View>
  );
}

/** A round icon button with a small label under it. */
function LabelledButton({ icon, label, onPress, disabled, filled, dashed, a11y }) {
  const th = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      hitSlop={6}
      accessibilityRole="button"
      accessibilityLabel={a11y || label}
      accessibilityState={{ disabled: !!disabled }}
      style={({ pressed }) => ({ width: 58, alignItems: 'center', gap: 4, opacity: pressed ? 0.75 : 1 })}
    >
      <View style={{
        width: 36, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center',
        backgroundColor: filled ? th.c.accent : 'transparent',
        borderWidth: filled ? 0 : 1.5, borderStyle: dashed ? 'dashed' : 'solid',
        borderColor: disabled ? th.c.hair2 : th.c.accent,
      }}>
        <Text style={[th.font.ui(700), { fontSize: 15, color: filled ? th.c.onAccent : disabled ? th.c.ink3 : th.c.accent }]}>{icon}</Text>
      </View>
      <Text numberOfLines={2} style={[th.font.ui(600), {
        fontSize: 9.5, lineHeight: 12, textAlign: 'center', color: disabled ? th.c.ink3 : filled ? th.c.accentDark : th.c.ink2,
      }]}>{label}</Text>
    </Pressable>
  );
}

/** Edit (Pro: `locked` shows ◆ and the caller opens the paywall). */
export function EditButton({ locked, onPress }) {
  const { t } = useI18n();
  return <LabelledButton icon="✎" label={locked ? `◆ ${t('remedies.edit')}` : t('remedies.edit')} onPress={onPress} />;
}

/** Done today: filled "Completed" (tap again to undo), outlined "Mark complete" when due, dashed when not due. */
export function DoneButton({ remedy: r, onPress }) {
  const { t } = useI18n();
  const done = r.today.completed;
  const due = r.due_today;
  if (done) return <LabelledButton icon="✓" filled label={t('remedies.completed')} onPress={onPress} a11y={t('remedies.undoA11y')} />;
  if (due) return <LabelledButton icon="✓" label={t('remedies.markComplete')} onPress={onPress} />;
  return <LabelledButton icon="–" dashed disabled label={t('remedies.notToday')} a11y={t('remedies.notDue')} />;
}
