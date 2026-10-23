# Guru Drishti — mobile app

Expo SDK 57 / React Native app (JavaScript, Expo Router) for the Django backend in `../backend`,
built to the **Antara** design in `../docs/design` (Newsreader / Hanken Grotesk / Spline Sans Mono,
tokenised light & dark themes, five tabs: Home · Timeline · Chart · Remedies · Profile).
It runs in **Expo Go** — no native build needed during development.

It stays on SDK 57 because the store Expo Go does not support SDK 58 yet. Once it does, upgrade with
`npm install expo@~58.0.0 && npx expo install --fix`, and replace `initialRouteName` in `src/app/(auth)/_layout.js`
with SDK 58's `anchor`.

## Run on your phone (Expo Go)

1. Start the backend so it listens on your network, not just localhost:
   ```bash
   cd ../backend && venv/Scripts/python manage.py runserver 0.0.0.0:8000
   ```
   If the phone can't connect, allow Python through Windows Firewall (private networks).
2. Start the app:
   ```bash
   npm install
   npx expo start -c
   ```
3. Scan the QR code with Expo Go (phone and PC on the same Wi-Fi).

In development the app reaches the backend at `http://<your PC's LAN IP>:8000` automatically (taken from the Metro host).
To use another server or tunnel mode, set `EXPO_PUBLIC_API_URL` in `.env` (see `.env.example`).
**Profile → Settings → About** shows the server in use. Verification codes are printed in the backend console.

Pro features (decision assistant, D9 & other divisions, deep Dasha levels, remedy tracking, transit alerts)
can be tried with the in-app 7-day trial, or granted with `python manage.py grant_pro you@example.com`.

## Customising (white-label)

Everything lives in **`brand.config.js`**:

| Section | What it controls |
|---|---|
| Identity | `name`, `slug`, `scheme`, `iosBundleIdentifier`, `androidPackage`, `version`, tagline, orb glyph |
| `assets` | icon, splash, adaptive icon, favicon |
| `apiUrl` / `devApiPort` | production backend URL, dev port |
| `theme.accent` | one of the design's accents: `dawn`, `twilight`, `grove`, `terracotta`, `amethyst`, `ink` (add your own in `theme.accents`) |
| `theme.base` | light background: `paper`, `sand`, `mist`, `fog`, `blush` |
| `features` | decision assistant, panchang, remedies, journal, alerts, paywall, South Indian chart, more divisions, birth details, Hindi, account deletion |
| `defaults` | language, theme mode, chart style, node mode, ayanamsa |

Users choose light/dark/system, English/हिन्दी and chart style in **Profile → Settings**.

## Structure

```
src/app/
  (auth)/          sign-in, sign-up (account + birth details), verify, forgot, reset
  (tabs)/index     Home — insight & why, current period, live transit, today's windows
  (tabs)/timeline/ day timeline · decision assistant · panchang
  (tabs)/chart/    kundali (+ house sheet) · dasha (5 levels) · strength · birth details
  (tabs)/remedies/ list + streak · remedy detail (count ring)
  (tabs)/profile/  charts you follow · journal · trends · alerts · settings
  paywall, profile/new, profile/edit/[id]   modals
src/components/    ui.js (design system), charts, LocationPicker, DateTimeField, TabBar, …
src/api/           fetch client (JWT refresh, Accept-Language) + endpoint functions
src/hooks/         useApi (shared cache) + data hooks
src/notifications.js  schedules the backend's alert feed as local notifications
src/i18n/          en.js, hi.js, terms.js (astrology vocabulary)
src/theme/         tokens from the design (accents, bases, dark palette, kinds, fonts)
```

## Checks

```bash
npx expo lint
npx expo-doctor
npx expo export --platform android
```
