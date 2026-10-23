import { Pressable, Text, View } from 'react-native';
import Svg, { G, Polygon, Rect, Text as SvgText, TSpan } from 'react-native-svg';

import { useI18n } from '../../i18n';
import { FONTS, useTheme } from '../../theme';

// Geometry from the design (300 × 300 viewBox).
const NPTS = {
  1: '150,0 225,75 150,150 75,75', 2: '0,0 150,0 75,75', 3: '0,0 75,75 0,150', 4: '0,150 75,75 150,150 75,225',
  5: '0,150 75,225 0,300', 6: '0,300 75,225 150,300', 7: '150,300 75,225 150,150 225,225', 8: '150,300 225,225 300,300',
  9: '300,300 225,225 300,150', 10: '300,150 225,225 150,150 225,75', 11: '300,150 225,75 300,0', 12: '300,0 225,75 150,0',
};
const NC = {
  1: [150, 58], 2: [75, 26], 3: [26, 78], 4: [64, 150], 5: [26, 224], 6: [75, 276],
  7: [150, 244], 8: [225, 276], 9: [276, 224], 10: [238, 150], 11: [276, 78], 12: [225, 26],
};
// South Indian fixed sign positions on the 4×4 grid: cell index -> sign (1 = Aries).
const SOUTH = { 0: 12, 1: 1, 2: 2, 3: 3, 4: 11, 7: 4, 8: 10, 11: 5, 12: 9, 13: 8, 14: 7, 15: 6 };
const SIGN_EN = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

/** Chart marks: * retrograde, ^ combust, ↑ exalted, ↓ debilitated. */
export function planetMarks(p) {
  return `${p.retrograde ? '*' : ''}${p.combust ? '^' : ''}${p.dignity === 'exalted' ? '↑' : p.dignity === 'debilitated' ? '↓' : ''}`;
}

/** Whole degrees within the sign, truncated (29°50′ → "29°", never "30°"). */
export const signDegree = (deg) => (deg == null ? '' : `${Math.floor(deg)}°`);

/**
 * Labels for one house/sign, `perRow` to a line: [[{text, muted}]]. Planets read "Su*" (or
 * "Su* 27°", sorted by degree, when `degrees` = {code: degree in sign} is given); `asc` adds a
 * muted "Asc 22°" first.
 */
function labelRows(planets, short, perRow, degrees, asc) {
  // With degrees, list planets in increasing order of degree (as they rise through the sign).
  const ordered = degrees ? [...planets].sort((a, b) => (degrees[a.code] ?? 0) - (degrees[b.code] ?? 0)) : planets;
  const items = ordered.map((p) => ({
    text: short(p.code) + planetMarks(p) + (degrees ? ` ${signDegree(degrees[p.code])}` : ''),
  }));
  if (asc) items.unshift({ text: asc, muted: true });
  const rows = [];
  for (let i = 0; i < items.length; i += perRow) rows.push(items.slice(i, i + perRow));
  return rows;
}

/**
 * varga: backend varga ({ascendant:{sign_index}, planets:[{code, sign_index, house}]}).
 * Houses are fixed (house 1 = top diamond); as in every North Indian chart, the number shown
 * in each house is its sign (1 = Aries … 12 = Pisces), counted on from the ascendant's sign.
 */
export function NorthChart({ varga, selected, onSelect, degrees }) {
  const th = useTheme();
  const { tr, t } = useI18n();
  const short = (c) => tr('planetShort', c);
  const signOf = (house) => ((varga.ascendant.sign_index - 1 + house - 1) % 12) + 1;
  const kendra = (n) => n === 1 || n === 4 || n === 7 || n === 10;
  // With degrees the labels are wider: 2 per line in the big diamonds, 1 in the triangles.
  const perRow = (n) => (degrees ? (kendra(n) ? 2 : 1) : kendra(n) ? 3 : 2);
  const ascLabel = degrees ? `${t('chart.asc')} ${signDegree(degrees.Asc)}` : null;
  return (
    <Svg viewBox="-1 -1 302 302" style={{ width: '100%', aspectRatio: 1 }}>
      <Rect x={1} y={1} width={298} height={298} fill="none" stroke={th.c.chartLine} strokeWidth={1.4} />
      {Object.keys(NPTS).map((k) => {
        const n = Number(k);
        const [cx, cy] = NC[n];
        const rows = labelRows(varga.planets.filter((p) => p.house === n), short, perRow(n), degrees, n === 1 ? ascLabel : null);
        const size = degrees ? 11 : 12.5;
        const lh = degrees ? 13 : 15;
        return (
          <G key={k} onPress={() => onSelect?.(n)}>
            <Polygon points={NPTS[k]} fill={selected === n ? th.soft(0.14) : 'rgba(0,0,0,0)'} stroke={th.c.chartLine} strokeWidth={1} />
            <SvgText x={cx} y={cy - 13 - (rows.length > 2 ? (rows.length - 2) * 5 : 0)} textAnchor="middle" fill={th.c.ink3} fontSize={10} fontFamily={FONTS.mono[400]}>{signOf(n)}</SvgText>
            {rows.map((r, i) => (
              <SvgText key={i} x={cx} y={cy + 8 + i * lh - (rows.length - 1) * (lh / 3)} textAnchor="middle" fontSize={size} fontWeight="700">
                {r.map((it, j) => (
                  <TSpan key={j} fill={it.muted ? th.c.ink2 : th.c.accent}>{(j ? ' ' : '') + it.text}</TSpan>
                ))}
              </SvgText>
            ))}
          </G>
        );
      })}
    </Svg>
  );
}

export function SouthChart({ varga, selected, onSelect, centerLabel, centerSub, degrees }) {
  const th = useTheme();
  const { tr, t } = useI18n();
  const asc = varga.ascendant.sign_index;
  const houseOf = (sign) => ((sign - asc + 12) % 12) + 1;
  return (
    <View style={{ width: '100%', aspectRatio: 1, borderWidth: 1, borderColor: th.c.chartLine }}>
      <View style={{ flex: 1, flexDirection: 'row', flexWrap: 'wrap' }}>
        {Array.from({ length: 16 }, (_, i) => {
          const sign = SOUTH[i];
          if (!sign) {
            return <View key={i} style={{ width: '25%', height: '25%' }} />;
          }
          const h = houseOf(sign);
          const rows = labelRows(varga.planets.filter((p) => p.sign_index === sign), (c) => tr('planetShort', c), degrees ? 1 : 2, degrees);
          return (
            <Pressable key={i} onPress={() => onSelect?.(h)} style={{
              width: '25%', height: '25%', borderWidth: 0.5, borderColor: th.c.chartLine, padding: 6,
              backgroundColor: selected === h ? th.soft(0.14) : 'transparent',
            }}>
              <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text numberOfLines={1} style={[th.font.ui(500), { fontSize: 8.5, letterSpacing: 0.5, textTransform: 'uppercase', color: th.c.ink3, flexShrink: 1 }]}>
                  {tr('sign', SIGN_EN[sign - 1])}
                </Text>
                {sign === asc ? (
                  <Text style={[th.font.ui(700), { fontSize: 8, color: th.c.accent }]}>
                    {t('chart.asc')}{degrees ? ` ${signDegree(degrees.Asc)}` : ''}
                  </Text>
                ) : null}
              </View>
              <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                {rows.map((r, k) => (
                  <Text key={k} numberOfLines={1} style={{ fontSize: degrees ? 11 : 12.5, fontWeight: '700', color: th.c.accent }}>
                    {r.map((it) => it.text).join(' ')}
                  </Text>
                ))}
              </View>
            </Pressable>
          );
        })}
      </View>
      <View pointerEvents="none" style={{
        position: 'absolute', left: '25%', top: '25%', width: '50%', height: '50%', alignItems: 'center', justifyContent: 'center',
        borderWidth: 0.5, borderColor: th.c.chartLine, backgroundColor: th.c.surface,
      }}>
        <Text style={[th.font.display(500), { fontSize: 22, color: th.c.accent }]}>{centerLabel}</Text>
        <Text style={[th.font.ui(500), { fontSize: 9, letterSpacing: 1, textTransform: 'uppercase', color: th.c.ink3 }]}>{centerSub}</Text>
      </View>
    </View>
  );
}
