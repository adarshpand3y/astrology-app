# Handoff: Antara — Vedic daily companion (mobile app)

## Overview
Antara is a Vedic astrology app for iOS and Android that people use every day. It focuses on **timing windows, decision guidance and a personalised daily insight** worked out from the user's birth chart (not sun-sign horoscopes). The tone is calm, premium and reflective: it offers guidance, not fixed predictions.

Bottom tabs: **Home / Timeline / Chart / Remedies / Profile**.

## About the design files
`Antara.dc.html` is a **design reference built in HTML**. It is an interactive prototype that shows the intended look and behaviour; it is not production code. Rebuild it in the target codebase's own stack and patterns (e.g. React Native / Expo, Flutter, or SwiftUI + Jetpack Compose). If no codebase exists yet, **React Native (Expo)** is a good fit: one codebase for both platforms, with a theme layer for light/dark mode and accent colours.

To view the prototype, open `Antara.dc.html` in a browser with `support.js` in the same folder (it needs internet access to load Google Fonts). The left rail switches screens, platform (iPhone/Android), theme (light/dark), accent colour and background colour.

All sample data is made up. **Chart placements, Shadbala and Bhavabala values are placeholders.** Real values must come from an ephemeris/astrology engine (e.g. Swiss Ephemeris). Dasha dates are computed with real Vimshottari arithmetic (see below).

## Fidelity
**High fidelity.** Colours, type, spacing, radii and interactions are final. Recreate them pixel-accurately. The phone frame is 390×844 pt (iPhone 14/15 class).

---

## Design tokens

### Colour — light (default background "Paper")
| Token | Value | Use |
|---|---|---|
| bg | `#F1ECE2` | screen canvas |
| surface | `#FFFFFF` | cards, inputs |
| surface2 | `#F4EFE6` | segmented track, muted chips |
| ink | `#26221C` | primary text |
| ink2 | `#6E685D` | secondary text |
| ink3 | `#A59E90` | tertiary / labels / mono captions |
| hairline | `rgba(38,34,28,.07–.12)` | 1px borders |
| hairline2 | `rgba(38,34,28,.14–.18)` | stronger outline / dashed |
| accent | `#B0722F` (Dawn) | CTAs, active states, links |
| accentDark | `#8A5A22` | accent text on tinted bg |
| onAccent | `#FFF8EE` | text on accent fill |
| accentSoft | accent @ 10–15% over transparent | info panels, chips |

### Colour — dark
bg `#100F17` · surface `#1C1B27` · surface2 `#25232F` · ink `#F0EDE6` · ink2 `#A6A0AE` · ink3 `#736D7C` · hairline `rgba(255,255,255,.10)` · hairline2 `rgba(255,255,255,.18)` · onAccent `#160F04` · shadows `0 18px 40px -22px rgba(0,0,0,.6)`.

### Accent options (pick one as the brand default; all tints are derived from it)
| Name | Light accent / dark | Dark-mode accent / dark |
|---|---|---|
| Dawn (default) | `#B0722F` / `#8A5A22` | `#DCA85F` / `#EBC48C` |
| Twilight | `#4C5BA6` / `#3B4890` | `#8E9BE0` / `#B2BBED` |
| Grove | `#5E8A6B` / `#496F56` | `#86B394` / `#A9CDB5` |
| Terracotta | `#B0654A` / `#8C4E38` | `#D89377` / `#E8AF97` |
| Amethyst | `#8A5A8F` / `#6D4372` | `#BE93C2` / `#D6B2D9` |
| Ink | `#566579` / `#404C5D` | `#93A2B8` / `#B4C0D0` |

Derived: soft tint = `color-mix(accent N%, transparent)` with N in {5,6,7,8,9,10,11,13,14,15,16,25}; gradient badge = `radial/linear(accent 45% mixed with white → accent)`; streak card = `linear-gradient(135deg, accent, accent 68% mixed with black)`.

### Light background options
| Name | bg | surface | surface2 |
|---|---|---|---|
| Paper (default) | `#F1ECE2` | `#FFFFFF` | `#F4EFE6` |
| Sand | `#ECE3D3` | `#FBF7EF` | `#F2EADB` |
| Mist | `#EBEDF1` | `#FFFFFF` | `#F2F3F6` |
| Fog | `#EAE7E1` | `#FBFAF7` | `#F1EEE8` |
| Blush | `#F1E8E3` | `#FFFDFB` | `#F6EEE9` |

### Semantic timing colours (same in both themes)
| Kind | Solid | Tint (backgrounds) | Label |
|---|---|---|---|
| Auspicious | `#5E8A6B` | `rgba(94,138,107,.13)` | "Auspicious" |
| Neutral | `#B08A3A` | `rgba(176,138,58,.14)` | "Neutral" |
| Inauspicious | `#B05A44` | `rgba(176,90,68,.13)` | "Avoid" |
Error text and borders use `#B05A44`.

### Typography
- **Display / editorial:** Newsreader (Google Fonts, optical size 6–72), weight 500, letter-spacing −0.2 to −0.3px. Used for screen titles (24px), the greeting (25px), the insight quote (22/1.32), large numbers (30–36px).
- **UI:** Hanken Grotesk 400/500/600/700.
- **Labels / data:** Spline Sans Mono 400–600. Eyebrow labels are 9–10.5px, UPPERCASE, letter-spacing 1–1.5px. Times and ranges are 10.5–12px.

| Role | Size / weight |
|---|---|
| Screen title | Newsreader 24 / 500 |
| Greeting | Newsreader 25 / 500 |
| Insight body | Newsreader 22 / 1.32 |
| Section title | 15–16 / 600 |
| Card title | 14–15.5 / 600 |
| Body | 12.5–13.5 / 400, line-height 1.5–1.6 |
| Secondary | 11–12 / 400 |
| Field label | 11.5 / 600 ink2 |
| Input text | 15 / 400 |
| Button | 15–15.5 / 600 |
| Tab label | 9.5 / 600 |

### Spacing, radius, elevation
- Screen side padding **20px** (sign-up / login **26px**). Bottom padding 120px so content clears the tab bar.
- Gaps: 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 22px. Card padding 14–20px.
- Radius: chip 20 (pill) · small tile 9–12 · input / button 13–14 · list card 15–17 · feature card 18–22 · bottom sheet 26 (top corners) · iOS screen 40 · Android screen 28.
- Shadows: hero card `0 18px 40px -22px rgba(20,16,30,.22)`; card `0 14px 34px -22px rgba(20,16,30,.2)`; primary CTA `0 8px 20px -8px accent@60%`; dropdown `0 12px 30px -8px rgba(20,16,30,.22)`; sheet `0 -14px 40px -14px rgba(20,16,30,.3)`.

### Iconography
- Grahas use typographic glyphs, never illustrations: Su ☉ · Mo ☽ · Ma ♂ · Me ☿ · Ju ♃ · Ve ♀ · Sa ♄ · Ra ☊ · Ke ☋. Shown in a 20–34px circle on an accent or semantic tint.
- Tab icons are 22px line icons with stroke 1.7 and round caps. Active = accent, inactive = `#A9A294`. SVG paths:
  - Home `M3 9.5 11 3l8 6.5V19a1 1 0 0 1-1 1h-4v-6H8v6H4a1 1 0 0 1-1-1z`
  - Timeline: circle r8 + `M11 6v5l3.5 2`
  - Chart `M11 2 20 11l-9 9-9-9zM11 2v18M2 11h18`
  - Remedies `M11 3c2 3 5 4.5 5 8a5 5 0 0 1-10 0c0-3.5 3-5 5-8z`
  - Profile: circle r3.6 at (11,7.5) + `M4.5 19c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6`
- Small markers: ◈ (guidance / "why"), ◐ ❋ ◆ ॐ (remedy types), ✈ ✎ ✚ (activities). In production, swap these for a custom icon set with the same weight.

### Motion
- Screen enter: fade + 6px rise, 0.5s ease.
- Expanding content ("why this", drill-downs): fade + −4px, 0.2–0.25s.
- Bottom sheet: translateY 100%→0, 0.3s `cubic-bezier(.2,.8,.2,1)`; scrim fades in over 0.25s.
- Logo orb "breathes": opacity .5↔.9 and scale 1↔1.04 over 5s, infinite.
- Toggles: 0.18s. Chevrons rotate 180° when open.

---

## Reusable components
1. **Insight card:** white, r22, padding 20. Eyebrow row (gradient sun badge + mono "TODAY'S INSIGHT"), Newsreader quote, hairline divider, then a **Why this?** row.
2. **"Why this" explainer:** tap the row to expand an accentSoft panel (r13) with the reasoning text plus graha chips. The chevron rotates.
3. **Graha chip:** pill with a 1px hairline2 border, 11px text, glyph + label (e.g. "☿ Budha ℞ Dasha").
4. **Timing-window block** (three variants by kind): tinted row, r15, 4px coloured bar on the left, name + gloss, a coloured kind label, and a mono time on the right.
5. **Timeline block:** 52px time column, then a 12px rail (11px dot with 2px tint ring and a 2px line), then a tinted card with a name, kind badge (pill, 1px solid@20%), gloss and range.
6. **Dasha / period row:** 32px glyph dot, name, Past/Now/Ahead tag, mono range, duration, chevron. *Now* has an accent border, 7% tint and a progress bar. *Past* is at 60% opacity.
7. **Streak tracker:** 7 day cells (flex 1, h30–34, r8–9). Done = accent fill, missed = muted.
8. **House-detail bottom sheet:** covers the screen. Scrim `rgba(20,16,30,.34)`, sheet r26, grabber 38×4, 46px number tile, title "{Karaka} · House n", sign · meaning, list of placements.
9. **Switch:** 42×25 track, 21px knob. On = accent, off = `rgba(38,34,28,.2)`.
10. **Segmented control:** each segment is flex 1, r10. Active has an accent border, 8% tint and accentDark text.
11. **Location picker:** see Sign up.

---

## Screens

### 01 Login
- Centred 64px breathing orb (☽), title "Welcome back", subtitle "Sign in to return to your sky."
- **Email** input and **Password** input with an inline Show/Hide text button (right 14px) and a "Forgot?" link next to the label.
- Primary CTA "Sign in", then an "or" divider ("New to Antara?") and an outlined button "Create an account" that goes to Sign up.
- Footer: Terms & Privacy, "Your birth details stay private to you."
- **Validation (on submit):** email must match `^\S+@\S+\.\S+$` and password must be ≥ 8 characters. A failing field gets a red border and an 11.5px red message ("Enter a valid email address" / "Password must be at least 8 characters"). If both pass, go to Home.

### 02 Sign up · birth details (onboarding)
- Orb, title "Create your account", subtitle about the chart being cast once.
- **ACCOUNT** section: Email and Password, with the same validation as Login.
- **BIRTH DETAILS** section: Name; Date of birth (flex 1.2) and Time (flex 1) side by side; a "I don't know my exact birth time — we'll use solar-sign methods" checkbox (20px, r6, accent when checked; the time shows "Unknown" in ink3).
- **Place of birth** and **Where you live now — sets your daily timings**: both are **restricted location pickers**.
  - Tap → the input clears to a search field (accent border) and a dropdown opens (max-height 212, scrolls, up to 8 matches, case-insensitive substring match on city or region).
  - Picking a row (on mouse/touch down) commits it. Clicking away without picking **reverts to the last valid choice**, so free text is never accepted.
  - No matches → "No supported location matches '…'. Pick the nearest city from the list."
  - Helper text while open: "Only supported locations can be selected — 28 cities available".
  - Supported list (id, city, region): blr Bengaluru, pnq Pune, bom Mumbai, del New Delhi, maa Chennai, hyd Hyderabad, ccu Kolkata, amd Ahmedabad, jai Jaipur, lko Lucknow, vns Varanasi, mys Mysuru, cok Kochi, trv Thiruvananthapuram, ixc Chandigarh, bbi Bhubaneswar, pat Patna, nag Nagpur, goi Panaji, ktm Kathmandu, cmb Colombo, sin Singapore, dxb Dubai, lon London, nyc New York, sfo San Francisco, yyz Toronto, syd Sydney. In production this should come from a backend list with lat/long/timezone.
- Trust line (accentSoft, r13): "Antara offers **guidance for reflection**, not fixed prediction. You always hold the choice."
- CTA "Create account & cast my chart" (validates email and password) → Home. Link: "Already have an account? **Sign in**" → Login.

### 03 Home / Daily (hero screen)
- Header: mono eyebrow "SATURDAY · 19 JULY" plus an accent pin with the **current location** ("Pune, Maharashtra", taken from the "Where you live now" choice); greeting "Good morning, Ananya" (Newsreader 25); 40px avatar (taps to Profiles).
- Insight card with "Why this?" (open by default in the prototype). Reasoning: Moon transiting the 4th house + Budha (Dasha lord) retrograde.
- Two equal cards: **Current period** "Budha–Shukra" with a progress bar (62%) and "1y 4m remaining", taps to Dasha; **Live transit** "Mars enters 10th", "Peaks around 3 PM", taps to Chart.
- "Today's windows" with a "Full timeline →" link, then three timing-window blocks (Abhijit Muhurta 11:58–12:49 good; Rahu Kaal 9:07–10:44 bad; Amrit Choghadiya 2:20–3:57 good).

### 04 Day timeline
Title, a ‹ Today › date pager, and a meta line (date, location, sunrise 6:02, sunset 6:47). A vertical list of timeline blocks: Sunrise·Amrit, Rog, Rahu Kaal, Gulika, Abhijit Muhurta, Char, Amrit, Yamaganda, Sunset, each colour-coded by kind. *Note: the location here is still hard-coded to Bengaluru and should follow the current location.*

### 05 Decision assistant
- Title "Best time to…". Activity chips (Travel ✈, Purchase ◈, Contract ✎, New venture ❋, Medical ✚); active = accent fill. Window segmented control: Today / Next 7 days / This month.
- CTA "Find my windows" shows **Ranked openings**: each row has a 46px score ring (r20, stroke 4, coloured by kind, score in the centre), the day + mono time, and a one-line reason. Sorted by score, highest first.

### 06 Kundali (birth chart)
- Segments: **North · diamond / South · grid**, and **Rāśi D1 / Navāmśa D9**.
- North: 300×300 SVG made of 12 polygons (house numbers in mono 10px ink3, graha glyphs 15px accent). South: 4×4 grid with the 12 outer cells as signs (fixed order: Pisces, Aries, Taurus, Gemini across the top row, and so on) and a centre block showing "D1/D9".
- Tap a house to open the house-detail bottom sheet. Graha legend chips below.
- Entry card "Strength · Ṣaḍbala & Bhāvabala" → Shadbala.

### 07 Dasha timeline (Vimshottari, 5 levels)
- **"You are in · now" card:** five indented rows (indent 12px per level). Each row has an eyebrow (Mahādaśā, Antardaśā, Pratyantardaśā, Sūkṣmadaśā, Prāṇadaśā), the chain name ("Budha › Shukra › …"), time left and a 54px progress bar. Tapping a row jumps the browser to that level.
- **Breadcrumb pills:** "All chapters › Budha › Shukra …". The last pill is solid accent; earlier ones are tinted and tappable.
- **Level header + proportional strip:** a 22px bar where each segment is sized by duration (past = muted, now = accent, ahead = tint), with a 2px "now" marker.
- **Period rows for the current level.** Tap to drill into the next level (down to Prāṇadaśā, which is the deepest).
- **Calculation:** order Ke, Ve, Su, Mo, Ma, Ra, Ju, Sa, Me with years 7, 20, 6, 10, 7, 18, 16, 19, 17 (total 120). A sub-period's length = parent length × child years / 120, starting from the parent's lord. Date formats by level: year · Mon YYYY · D Mon 'YY · D Mon 'YY · D Mon, HH:MM. Durations shown as "Xy Ym" / "Xm Yd" / "Xd Yh" / "Xh Ym". The prototype's Mahādaśā start is chosen so 'now' falls in Budha–Shukra; in production, derive it from the Moon's nakshatra position at birth.

### 08 Strength · Ṣaḍbala (planets) and 09 Bhāvabala (houses)
One screen with a segmented switch between the two; back link to Kundali.
- **Shadbala:** summary card ("4 / 7 grahas at full strength", strongest and weakest chips, a note about the Dasha lord). Rows are sorted by strength ratio = total rūpas ÷ required minimum. Each row shows the glyph in a semantic tint, name, "x.x rūpas · needs y.y", the ratio and its status (≥1.10 Strong / ≥1.00 Adequate / <1.00 Needs support), and a 6px bar with a minimum marker at 62.5%. Tap to expand: a 2-column grid of the **six sources** (Sthāna, Dig, Kāla, Ceṣṭā, Naisargika, Dṛk) in virūpas with mini bars, then a **What to do** panel (a headline + 2–4 actions). Weak grahas also get an "Add to my remedies" CTA.
- **Bhavabala:** a 12-bar chart (130px tall, dashed line at the 7.0 rūpa minimum, colour by ≥8 / ≥7 / <7; the selected bar is fully opaque with an accent ring). Tap a bar to show its detail card: house number tile, karaka/sign/meaning, value + status, three component tiles (lord 56% · direction 29% · aspects 15%), a **house lord** row linking to that graha's Shadbala, and a **What to do** list.

### 10 Panchang
Date pager; almanac card with an accentSoft header (location, Śaka/month, sunrise/sunset/moonrise) and 5 rows (Tithi, Vāra, Nakshatra, Yoga, Karana), each with a kind dot, label + gloss, value + detail. Below it, an interpretation note.

### 11 Remedies and 12 Remedy detail
- Streak card (accent gradient, r20): "12 days", "Best: 21 days", and 7 day cells. Remedy rows (Mantra ॐ, Fasting ◐, Charity ❋, Gemstone ◆), each with a reminder switch; tap a row to open its detail.
- Detail: 150px progress ring (r66, stroke 10, 72/108), mantra name and transliteration, a "How & why" card, the week's streak, and a "Mark today complete" CTA.

### 13 Journal and 14 Trends
- Journal: 5 mood tiles (Heavy ☁ · Low ◔ · Even ◑ · Good ◕ · Bright ☀), "What shaped it?" tag chips, a free-text area, and a Save CTA → Trends.
- Trends: a 14-day mood bar chart (height = value × 17px, coloured by value) and two insight cards that link mood to timing windows and weekdays.

### 15 Profiles
Rows with a 42px coloured initials avatar, name, relationship pill and birth info; the active row has an accent border and ✓. A dashed "+ Add a birth profile" row.

### 16 Alerts
- Push previews (frosted cards, 32px coloured app tile, title, time, body).
- Settings list with switches: Dasha & sub-period changes, Transit hits, Rahu Kāl reminder (15 min before), Sade Sati entry & exit, Daily insight (8:00 AM).

### 17 Paywall (no tab bar)
Close ✕, orb, "Read your sky, every single day". A Monthly/Annual toggle (Annual is the default and emphasised): **₹2,499/yr** ("≈ ₹208 / month · save 30%") or **₹299/mo**, with a "7-day free trial" pill. A Free vs Pro comparison table (8 rows), a "Start free trial" CTA, "Buy a one-off report →", and Restore · Terms · Privacy.

---

## Navigation and state
- The tab bar is hidden on Login, Sign up and Paywall. Active tab mapping: Timeline ← timeline, decision, panchang; Chart ← chart, dasha, shadbala, bhavabala; Remedies ← remedies, remedyDetail; Profile ← journal, trends, profiles, notifications.
- **Platform differences:** iOS has a 54pt status bar with a Dynamic Island, a 22pt tab-bar bottom inset and a 138×5 home indicator. Android has a 40dp status bar, a 12dp inset and a 110×4 gesture bar. Use the native safe-area insets in production.
- **State to model:** `theme`, `accent`, `base`, auth (`email`, `password`, `showPassword`, `submitted`), birth profile (`name`, `dob`, `tob | unknown`, `birthLocationId`, `currentLocationId`), `whyOpen`, decision (`activity`, `range`, results), chart (`style`, `varga`, `selectedHouse`), dasha `path` (array of lord keys, up to 4 deep), strength (`selectedPlanet`, `selectedHouse`), remedy reminders + completions, journal (`rating`, tags, note), alert toggles, `billing`.
- **Data needed from the backend / engine:** sidereal planetary positions (Lahiri ayanamsa), house cusps, D9 positions, Vimshottari dasha tree, Shadbala/Bhavabala, daily Panchang + Rahu Kaal/Yamaganda/Gulika/Abhijit/Choghadiya for the **current location** (sunrise-based), transits, plus a ranking service for the decision assistant.

## Assets
No raster images. Fonts are Newsreader, Hanken Grotesk and Spline Sans Mono, all from Google Fonts. Icons are inline SVG paths plus Unicode glyphs (listed above).

## Files
- `Antara.dc.html`: the full interactive prototype (template markup + a logic class holding all mock data and calculations).
- `support.js`: the runtime the prototype needs to open in a browser. It is not needed for implementation.
