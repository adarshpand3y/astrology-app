// Design-system primitives for the "Antara" design language.
import { useRouter } from 'expo-router';
import { forwardRef, useEffect, useState } from 'react';
import {
  ActivityIndicator, Animated, Easing, Modal, Pressable, RefreshControl, ScrollView, StyleSheet, Text, TextInput, View,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, LinearGradient, RadialGradient, Rect, Stop } from 'react-native-svg';

import { useI18n } from '../i18n';
import { ERROR, useTheme } from '../theme';
import { errorMessage } from '../utils/format';

// --- Text -------------------------------------------------------------------------------
const VARIANTS = {
  screenTitle: (th) => ({ ...th.font.display(500), fontSize: 24, color: th.c.ink, letterSpacing: -0.3 }),
  greeting: (th) => ({ ...th.font.display(500), fontSize: 25, color: th.c.ink, letterSpacing: -0.3 }),
  heroTitle: (th) => ({ ...th.font.display(500), fontSize: 27, color: th.c.ink, letterSpacing: -0.3 }),
  quote: (th) => ({ ...th.font.display(400), fontSize: 22, lineHeight: 29, color: th.c.ink, letterSpacing: -0.2 }),
  number: (th) => ({ ...th.font.display(500), fontSize: 30, color: th.c.ink }),
  section: (th) => ({ ...th.font.ui(600), fontSize: 15, color: th.c.ink }),
  cardTitle: (th) => ({ ...th.font.ui(600), fontSize: 14.5, color: th.c.ink }),
  body: (th) => ({ ...th.font.ui(400), fontSize: 13.5, lineHeight: 20, color: th.c.ink }),
  small: (th) => ({ ...th.font.ui(400), fontSize: 12.5, lineHeight: 19, color: th.c.ink2 }),
  caption: (th) => ({ ...th.font.ui(400), fontSize: 11.5, lineHeight: 16.5, color: th.c.ink2 }),
  tiny: (th) => ({ ...th.font.ui(400), fontSize: 11, color: th.c.ink3 }),
  label: (th) => ({ ...th.font.ui(600), fontSize: 11.5, color: th.c.ink2 }),
  eyebrow: (th) => ({ ...th.font.mono(500), fontSize: 9.5, letterSpacing: 1.2, textTransform: 'uppercase', color: th.c.ink3 }),
  mono: (th) => ({ ...th.font.mono(400), fontSize: 11, color: th.c.ink3 }),
  link: (th) => ({ ...th.font.ui(600), fontSize: 12, color: th.c.accent }),
};

export function T({ v = 'body', style, color, weight, children, ...rest }) {
  const th = useTheme();
  const base = VARIANTS[v](th);
  const w = weight ? th.font.ui(weight) : null;
  return <Text style={[base, w, color && { color }, style]} {...rest}>{children}</Text>;
}

/** Renders "**bold**" segments with ink colour + semibold weight (the design's <b>). */
export function Rich({ text, v = 'small', style, boldColor }) {
  const th = useTheme();
  const parts = String(text || '').split(/(\*\*[^*]+\*\*)/g);
  return (
    <T v={v} style={style}>
      {parts.map((p, i) => (p.startsWith('**')
        ? <Text key={i} style={[th.font.ui(600), { color: boldColor || th.c.ink }]}>{p.slice(2, -2)}</Text>
        : p))}
    </T>
  );
}

// --- Layout -------------------------------------------------------------------------------
export function FadeIn({ children, style, delay = 0 }) {
  const [a] = useState(() => new Animated.Value(0));
  useEffect(() => {
    Animated.timing(a, { toValue: 1, duration: 450, delay, easing: Easing.out(Easing.ease), useNativeDriver: true }).start();
  }, [a, delay]);
  return (
    <Animated.View style={[{ opacity: a, transform: [{ translateY: a.interpolate({ inputRange: [0, 1], outputRange: [6, 0] }) }] }, style]}>
      {children}
    </Animated.View>
  );
}

/**
 * Scrollable screen with the design's 20px gutter. Wrapped in a SafeAreaView so the
 * status bar / notch / home indicator areas stay clear while content scrolls beneath.
 * On tab screens the tab bar handles the bottom inset itself.
 */
/** Content top padding inside Screen's scroll view (for pages that scroll to a child). */
export const SCREEN_TOP_PAD = 10;

export function Screen({ children, refreshing, onRefresh, tabs = true, gutter = 20, top = true, footer, scrollRef }) {
  const th = useTheme();
  const edges = ['left', 'right', ...(top ? ['top'] : []), ...(tabs ? [] : ['bottom'])];
  return (
    <SafeAreaView edges={edges} style={{ flex: 1, backgroundColor: th.c.bg }}>
      <ScrollView
        ref={scrollRef}
        contentContainerStyle={{ paddingHorizontal: gutter, paddingTop: SCREEN_TOP_PAD, paddingBottom: tabs ? 40 : 34 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        refreshControl={onRefresh ? <RefreshControl refreshing={!!refreshing} onRefresh={onRefresh} tintColor={th.c.accent} /> : undefined}
      >
        <FadeIn>{children}</FadeIn>
      </ScrollView>
      {footer}
    </SafeAreaView>
  );
}

export function Card({ children, style, radius = 20, pad = 16, shadow, onPress, border }) {
  const th = useTheme();
  const box = [{
    backgroundColor: th.c.surface, borderRadius: radius, padding: pad, borderWidth: 1,
    borderColor: border || th.c.hair,
  }, shadow && th.shadow(shadow === true ? 'card' : shadow), style];
  if (onPress) {
    return <Pressable onPress={onPress} style={({ pressed }) => [box, pressed && { opacity: 0.85 }]}>{children}</Pressable>;
  }
  return <View style={box}>{children}</View>;
}

export function Row({ children, style, gap = 8, align = 'center' }) {
  return <View style={[{ flexDirection: 'row', alignItems: align, gap }, style]}>{children}</View>;
}

export function Divider({ style }) {
  const th = useTheme();
  return <View style={[{ height: 1, backgroundColor: th.c.hair }, style]} />;
}

export function ScreenHeader({ title, sub, right, back, onBack }) {
  return (
    <View style={{ paddingHorizontal: 2, paddingBottom: sub ? 16 : 14 }}>
      {back ? <BackLink label={back} onPress={onBack} /> : null}
      <Row style={{ justifyContent: 'space-between', alignItems: 'center' }}>
        <T v="screenTitle" style={{ flex: 1 }}>{title}</T>
        {right}
      </Row>
      {sub ? <T v="small" style={{ marginTop: 3 }}>{sub}</T> : null}
    </View>
  );
}

export function BackLink({ label, onPress }) {
  const th = useTheme();
  const router = useRouter();
  return (
    <Pressable onPress={onPress || (() => router.back())} hitSlop={10} style={{ flexDirection: 'row', alignItems: 'center', gap: 6, paddingBottom: 10 }}>
      <T style={{ fontSize: 16, color: th.c.ink2 }}>‹</T>
      <T v="small" style={{ fontSize: 13 }}>{label}</T>
    </Pressable>
  );
}

// --- Buttons ------------------------------------------------------------------------------
export function Button({ title, onPress, variant = 'primary', loading, disabled, style, small }) {
  const th = useTheme();
  const primary = variant === 'primary';
  const danger = variant === 'danger';
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [{
        backgroundColor: primary ? th.c.accent : danger ? ERROR : 'transparent',
        borderWidth: primary || danger ? 0 : 1, borderColor: th.c.hair2,
        borderRadius: small ? 11 : 14, paddingVertical: small ? 11 : 15.5, paddingHorizontal: 16,
        alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: 8,
        opacity: disabled ? 0.5 : pressed ? 0.88 : 1,
      }, primary && !disabled && th.shadow('cta'), style]}
    >
      {loading ? <ActivityIndicator color={primary || danger ? th.c.onAccent : th.c.ink} /> : null}
      <Text style={[th.font.ui(600), { fontSize: small ? 13 : 15.5, color: primary ? th.c.onAccent : danger ? '#fff' : th.c.ink }]}>
        {title}
      </Text>
    </Pressable>
  );
}

export function TextLink({ title, onPress, style }) {
  return (
    <Pressable onPress={onPress} hitSlop={8}>
      <T v="link" style={style}>{title}</T>
    </Pressable>
  );
}

// --- Inputs ---------------------------------------------------------------------------------
export const Field = forwardRef(function Field({ label, labelRight, error, style, inputStyle, right, focused, ...props }, ref) {
  const th = useTheme();
  const [focus, setFocus] = useState(false);
  return (
    <View style={style}>
      {label ? (
        <Row style={{ justifyContent: 'space-between', marginBottom: 6 }}>
          <T v="label">{label}</T>
          {labelRight}
        </Row>
      ) : null}
      <View>
        <TextInput
          ref={ref}
          placeholderTextColor={th.c.ink3}
          style={[th.font.ui(400), {
            backgroundColor: th.c.surface, borderWidth: 1,
            borderColor: error ? ERROR : (focus || focused) ? th.c.accent : th.c.hair2,
            borderRadius: 13, paddingHorizontal: 15, paddingVertical: 14, fontSize: 15, color: th.c.ink,
            paddingRight: right ? 64 : 15,
          }, inputStyle]}
          {...props}
          onFocus={(e) => { setFocus(true); props.onFocus?.(e); }}
          onBlur={(e) => { setFocus(false); props.onBlur?.(e); }}
        />
        {right ? <View style={{ position: 'absolute', right: 14, top: 0, bottom: 0, justifyContent: 'center' }}>{right}</View> : null}
      </View>
      {error ? <T v="caption" style={{ color: ERROR, marginTop: 6 }}>{error}</T> : null}
    </View>
  );
});

export function PasswordField(props) {
  const { t } = useI18n();
  const [show, setShow] = useState(false);
  return (
    <Field
      {...props}
      secureTextEntry={!show}
      autoCapitalize="none"
      right={<Pressable hitSlop={8} onPress={() => setShow((s) => !s)}><T v="tiny" weight={600} style={{ fontSize: 12 }}>{show ? t('auth.hide') : t('auth.show')}</T></Pressable>}
    />
  );
}

/** Read-only field box that opens a picker (date / time). */
export function FieldBox({ label, value, placeholder, onPress, muted, style, error }) {
  const th = useTheme();
  return (
    <View style={style}>
      {label ? <T v="label" style={{ marginBottom: 6 }}>{label}</T> : null}
      <Pressable onPress={onPress} style={{
        backgroundColor: th.c.surface, borderWidth: 1, borderColor: error ? ERROR : th.c.hair2, borderRadius: 13,
        paddingHorizontal: 15, paddingVertical: 14,
      }}>
        <T style={{ fontSize: 15, color: muted || !value ? th.c.ink3 : th.c.ink }}>{value || placeholder}</T>
      </Pressable>
      {typeof error === 'string' ? <T v="caption" style={{ color: ERROR, marginTop: 6 }}>{error}</T> : null}
    </View>
  );
}

export function Checkbox({ checked, onChange, children }) {
  const th = useTheme();
  return (
    <Pressable onPress={() => onChange(!checked)} style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }} hitSlop={6}>
      <View style={{
        width: 20, height: 20, borderRadius: 6, borderWidth: 1.5, alignItems: 'center', justifyContent: 'center',
        borderColor: checked ? th.c.accent : th.c.hair2, backgroundColor: checked ? th.c.accent : 'transparent',
      }}>
        {checked ? <Text style={{ color: '#fff', fontSize: 12 }}>✓</Text> : null}
      </View>
      <View style={{ flex: 1 }}>{children}</View>
    </Pressable>
  );
}

export function Switch({ value, onChange, disabled }) {
  const th = useTheme();
  const [a] = useState(() => new Animated.Value(value ? 1 : 0));
  useEffect(() => { Animated.timing(a, { toValue: value ? 1 : 0, duration: 180, useNativeDriver: false }).start(); }, [a, value]);
  return (
    <Pressable onPress={() => !disabled && onChange(!value)} hitSlop={8} accessibilityRole="switch" accessibilityState={{ checked: value }}>
      <Animated.View style={{
        width: 42, height: 25, borderRadius: 14, padding: 2, justifyContent: 'center', opacity: disabled ? 0.5 : 1,
        backgroundColor: a.interpolate({ inputRange: [0, 1], outputRange: [th.dark ? 'rgba(255,255,255,.2)' : 'rgba(38,34,28,.2)', th.c.accent] }),
      }}>
        <Animated.View style={{
          width: 21, height: 21, borderRadius: 11, backgroundColor: '#fff', ...th.shadow('card'), elevation: 2,
          transform: [{ translateX: a.interpolate({ inputRange: [0, 1], outputRange: [0, 17] }) }],
        }} />
      </Animated.View>
    </Pressable>
  );
}

/** The design's segmented control: each option flex 1, active = accent border + 8% tint. */
export function Seg({ options, value, onChange, style, lockedValues = [] }) {
  const th = useTheme();
  return (
    <Row gap={8} style={style}>
      {options.map((o) => {
        const active = o.value === value;
        return (
          <Pressable key={String(o.value)} onPress={() => onChange(o.value)} style={{
            flex: 1, alignItems: 'center', paddingVertical: 10, paddingHorizontal: 6, borderRadius: 10, borderWidth: 1,
            borderColor: active ? th.c.accent : th.c.hair2, backgroundColor: active ? th.soft(0.08) : 'transparent',
          }}>
            <Text numberOfLines={1} style={[th.font.ui(600), { fontSize: 13, color: active ? th.c.accentDark : th.c.ink2 }]}>
              {o.label}{lockedValues.includes(o.value) ? '  ◆' : ''}
            </Text>
          </Pressable>
        );
      })}
    </Row>
  );
}

/** Activity chip (filled when active). */
export function Chip({ label, glyph, active, onPress }) {
  const th = useTheme();
  return (
    <Pressable onPress={onPress} style={{
      flexDirection: 'row', alignItems: 'center', gap: 7, paddingVertical: 9, paddingHorizontal: 14, borderRadius: 12,
      borderWidth: 1, borderColor: active ? th.c.accent : th.c.hair2, backgroundColor: active ? th.c.accent : 'transparent',
    }}>
      {glyph ? <Text style={{ fontSize: 15, color: active ? th.c.onAccent : th.c.ink2 }}>{glyph}</Text> : null}
      <Text style={[th.font.ui(600), { fontSize: 13, color: active ? th.c.onAccent : th.c.ink2 }]}>{label}</Text>
    </Pressable>
  );
}

/** Outline pill (graha chip / legend). */
export function Pill({ children, style, surface, onPress }) {
  const th = useTheme();
  const Comp = onPress ? Pressable : View;
  return (
    <Comp onPress={onPress} style={[{
      flexDirection: 'row', alignItems: 'center', gap: 5, paddingVertical: 5, paddingHorizontal: 9, borderRadius: 20,
      borderWidth: 1, borderColor: surface ? th.c.hair : th.c.hair2, backgroundColor: surface ? th.c.surface : 'transparent',
    }, style]}>
      {typeof children === 'string' ? <T v="tiny" style={{ color: th.c.ink2 }}>{children}</T> : children}
    </Comp>
  );
}

export function Tag({ children, tone }) {
  const th = useTheme();
  return (
    <View style={{ paddingVertical: 2, paddingHorizontal: 7, borderRadius: 20, backgroundColor: tone ? th.kind[tone].tint : th.c.muted }}>
      <T v="tiny" style={{ fontSize: 10, color: tone ? th.kind[tone].solid : th.c.ink2 }}>{children}</T>
    </View>
  );
}

// --- Decorations ----------------------------------------------------------------------------
export function Orb({ size = 64, glyph = '☽' }) {
  const th = useTheme();
  const [a] = useState(() => new Animated.Value(0));
  useEffect(() => {
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(a, { toValue: 1, duration: 2500, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      Animated.timing(a, { toValue: 0, duration: 2500, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [a]);
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Animated.View style={{
        position: 'absolute', width: size, height: size,
        opacity: a.interpolate({ inputRange: [0, 1], outputRange: [0.5, 0.9] }),
        transform: [{ scale: a.interpolate({ inputRange: [0, 1], outputRange: [1, 1.04] }) }],
      }}>
        <Svg width={size} height={size}>
          <Defs>
            <RadialGradient id="orb" cx="50%" cy="40%" r="60%">
              <Stop offset="0" stopColor={th.gradient[0]} />
              <Stop offset="1" stopColor={th.gradient[1]} />
            </RadialGradient>
          </Defs>
          <Circle cx={size / 2} cy={size / 2} r={size / 2} fill="url(#orb)" />
        </Svg>
      </Animated.View>
      <Text style={{ fontSize: size * 0.4, color: '#fff' }}>{glyph}</Text>
    </View>
  );
}

/** Small gradient circle with a glyph (insight badge). */
export function GradientBadge({ size = 22, glyph = '☉' }) {
  const th = useTheme();
  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
        <Defs>
          <LinearGradient id="gb" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={th.gradient[0]} />
            <Stop offset="1" stopColor={th.gradient[1]} />
          </LinearGradient>
        </Defs>
        <Circle cx={size / 2} cy={size / 2} r={size / 2} fill="url(#gb)" />
      </Svg>
      <Text style={{ fontSize: size * 0.55, color: '#fff' }}>{glyph}</Text>
    </View>
  );
}

/** Accent→dark gradient panel (streak card). */
export function GradientPanel({ children, style }) {
  const th = useTheme();
  // A fixed 100×100 drawing stretched over the panel (preserveAspectRatio="none") paints the
  // gradient on the first frame without measuring the panel; percentage sizes on the SVG root
  // don't resolve reliably. The solid accent background covers the instant before it paints.
  return (
    <View style={[{ borderRadius: 20, overflow: 'hidden', backgroundColor: th.c.accent }, th.shadow('cta'), style]}>
      <Svg viewBox="0 0 100 100" preserveAspectRatio="none" style={StyleSheet.absoluteFill}>
        <Defs>
          <LinearGradient id="gp" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
            <Stop offset="0" stopColor={th.c.accent} />
            <Stop offset="1" stopColor={th.deep} />
          </LinearGradient>
        </Defs>
        <Rect x="0" y="0" width="100" height="100" fill="url(#gp)" />
      </Svg>
      {children}
    </View>
  );
}

/** Circle holding a symbol or a short text label (planet abbreviations like "Su" / "सू"). */
export function GlyphDot({ glyph, size = 32, bg, color, fontSize }) {
  const text = String(glyph ?? '').length > 1;
  const fs = text ? Math.min(fontSize || Infinity, size * 0.4) : fontSize || size * 0.47;
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: bg, alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ fontSize: fs, color, fontWeight: text ? '700' : undefined }}>{glyph}</Text>
    </View>
  );
}

export function Avatar({ initials, color, size = 42, onPress }) {
  const th = useTheme();
  const Comp = onPress ? Pressable : View;
  return (
    <Comp onPress={onPress} style={{
      width: size, height: size, borderRadius: size / 2, alignItems: 'center', justifyContent: 'center',
      backgroundColor: color || th.c.avatarBg, borderWidth: color ? 0 : 1, borderColor: th.c.hair,
    }}>
      <Text style={[th.font.ui(600), { fontSize: 14, color: color ? '#fff' : th.c.avatarFg }]}>{initials}</Text>
    </Comp>
  );
}

export function Bar({ value, color, height = 4, track, style }) {
  const th = useTheme();
  return (
    <View style={[{ height, borderRadius: height, backgroundColor: track || th.c.track, overflow: 'hidden' }, style]}>
      <View style={{ width: `${Math.max(0, Math.min(1, value || 0)) * 100}%`, height: '100%', borderRadius: height, backgroundColor: color || th.c.accent }} />
    </View>
  );
}

/** Coloured timing-window row (home summary). */
export function WindowRow({ name, gloss, label, time, kind }) {
  const th = useTheme();
  const k = th.kind[kind];
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 13, paddingHorizontal: 14, borderRadius: 15, backgroundColor: k.tint, marginBottom: 8 }}>
      <View style={{ width: 4, height: 34, borderRadius: 3, backgroundColor: k.solid }} />
      <View style={{ flex: 1 }}>
        <Text style={[th.font.ui(600), { fontSize: 14, color: th.c.ink }]}>
          {name} <Text style={[th.font.ui(400), { fontSize: 11.5, color: th.c.ink3 }]}>{gloss}</Text>
        </Text>
        <T v="tiny" weight={600} style={{ color: k.solid, marginTop: 2 }}>{label}</T>
      </View>
      <T v="mono" style={{ fontSize: 12, color: k.solid }}>{time}</T>
    </View>
  );
}

export function SoftPanel({ children, style, n = 0.11 }) {
  const th = useTheme();
  return <View style={[{ backgroundColor: th.soft(n), borderRadius: 13, paddingVertical: 12, paddingHorizontal: 14 }, style]}>{children}</View>;
}

/** "◈ What to do" panel heading */
export function PanelHeading({ children, glyph = '◈' }) {
  const th = useTheme();
  return (
    <Row gap={7} style={{ marginBottom: 6 }}>
      <Text style={{ color: th.c.accent, fontSize: 13 }}>{glyph}</Text>
      <T weight={700} style={{ fontSize: 12, color: th.c.accentDark }}>{children}</T>
    </Row>
  );
}

export function Bullet({ title, detail, children }) {
  const th = useTheme();
  return (
    <Row align="flex-start" gap={10} style={{ paddingVertical: 6 }}>
      <View style={{ width: 5, height: 5, borderRadius: 3, backgroundColor: th.c.accent, marginTop: 7 }} />
      <View style={{ flex: 1 }}>
        {title ? <T weight={600} style={{ fontSize: 12.5 }}>{title}</T> : null}
        {detail ? <T v="small" style={{ fontSize: 12, lineHeight: 17, marginTop: 1 }}>{detail}</T> : null}
        {children}
      </View>
    </Row>
  );
}

// --- States ---------------------------------------------------------------------------------
export function Loading({ style }) {
  const th = useTheme();
  return (
    <View style={[{ paddingVertical: 60, alignItems: 'center' }, style]}>
      <ActivityIndicator color={th.c.accent} />
    </View>
  );
}

export function FullLoading() {
  const th = useTheme();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: th.c.bg, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator color={th.c.accent} />
    </SafeAreaView>
  );
}

export function ErrorView({ error, onRetry, style }) {
  const th = useTheme();
  const { t } = useI18n();
  if (!error) return null;
  return (
    <View style={[{ backgroundColor: th.kind.bad.tint, borderRadius: 13, padding: 13, marginBottom: 12 }, style]}>
      <T v="small" style={{ color: ERROR }}>{errorMessage(error, t)}</T>
      {onRetry ? <TextLink title={t('common.retry')} onPress={onRetry} style={{ marginTop: 6 }} /> : null}
    </View>
  );
}

export function Empty({ title, sub, action }) {
  return (
    <View style={{ alignItems: 'center', paddingVertical: 40, paddingHorizontal: 10 }}>
      <Orb size={52} />
      <T v="section" style={{ marginTop: 14, textAlign: 'center' }}>{title}</T>
      {sub ? <T v="small" style={{ textAlign: 'center', marginTop: 6 }}>{sub}</T> : null}
      {action ? <View style={{ marginTop: 16, alignSelf: 'stretch' }}>{action}</View> : null}
    </View>
  );
}

/** Upsell card shown when the API answers `pro_required`. */
export function ProLock({ text }) {
  const { t } = useI18n();
  const router = useRouter();
  return (
    <SoftPanel style={{ borderRadius: 16, padding: 16, marginVertical: 8 }} n={0.1}>
      <PanelHeading glyph="◆">{t('common.pro')}</PanelHeading>
      <T v="small" style={{ marginBottom: 10 }}>{text}</T>
      <Button small title={t('common.unlock')} onPress={() => router.push('/paywall')} />
    </SoftPanel>
  );
}

// --- Bottom sheet -----------------------------------------------------------------------------
export function Sheet({ visible, onClose, children }) {
  const th = useTheme();
  const insets = useSafeAreaInsets();
  const [y] = useState(() => new Animated.Value(1));
  useEffect(() => {
    if (visible) {
      y.setValue(1);
      Animated.timing(y, { toValue: 0, duration: 300, easing: Easing.bezier(0.2, 0.8, 0.2, 1), useNativeDriver: true }).start();
    }
  }, [visible, y]);
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose} statusBarTranslucent>
      <View style={{ flex: 1, justifyContent: 'flex-end' }}>
        <Pressable style={[StyleSheet.absoluteFill, { backgroundColor: th.c.scrim }]} onPress={onClose} />
        <Animated.View style={[{
          backgroundColor: th.c.sheet, borderTopLeftRadius: 26, borderTopRightRadius: 26,
          paddingHorizontal: 22, paddingTop: 10, paddingBottom: insets.bottom + 26,
          transform: [{ translateY: y.interpolate({ inputRange: [0, 1], outputRange: [0, 600] }) }],
        }, th.shadow('sheet')]}>
          <View style={{ width: 38, height: 4, borderRadius: 3, backgroundColor: th.c.hair2, alignSelf: 'center', marginTop: 4, marginBottom: 16 }} />
          {children}
        </Animated.View>
      </View>
    </Modal>
  );
}
