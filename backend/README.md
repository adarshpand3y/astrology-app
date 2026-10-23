# Astrology backend

Django 6.1 modular monolith serving a JSON API for a mobile app: email/JWT auth,
birth profiles, place search, a Vedic astrology engine (birth chart, panchang,
avakhada, 16 divisional charts, 5-level Vimshottari dasha, Shadbala, Bhava Bala) and
the daily companion features (insight, muhurta timings, transits, decision assistant,
remedies, journal, alerts, Pro plan). Generated texts are available in English and Hindi
(send `Accept-Language: hi`).

## Quick start

```bash
python -m venv venv && venv/Scripts/activate      # Windows; use bin/activate elsewhere
pip install -r requirements.txt
cp .env.example .env
python manage.py download_ephemeris               # JPL DE440s, ~32 MB (1849–2150)
python manage.py load_places                      # GeoNames cities5000, ~70k places
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Test UI: http://localhost:8000/ui/ (OTP codes are printed to the runserver console)
- API docs (Swagger): http://localhost:8000/api/docs/ · schema: `/api/schema/`
- Health: `/healthz` · Admin: `/admin/`

Tests: `pytest` (uses `astrology.settings.test`).

## Layout

```
astrology/settings/{base,dev,prod,test}.py   env-driven settings
apps/core        error envelope, throttles, pagination, health
apps/accounts    custom User (email login), OTP email verification, JWT
apps/places      GeoNames Place model, search, timezone resolution
apps/profiles    BirthProfile CRUD (many per user)
apps/vedic       engine/ (pure Python, no Django) + content/ (bilingual texts) + services + API
apps/daily       home, day timeline, panchang, decision assistant, transits
apps/remedies    goal-based, editable remedies, reminders, counts, streaks, history
apps/journal     mood check-ins and timing-linked trends
apps/alerts      alert preferences + upcoming-notification feed (scheduled on the phone)
apps/billing     plan / trial / Pro gating (store billing plugs in later)
apps/web         template test UI that calls the same API as the mobile app
```

Each app owns its models, URLs and services; cross-app calls go through `services.py`.
`apps/vedic/engine` has no Django imports and can be reused or extracted as-is.

## API (prefix `/api/v1`)

All endpoints except auth require `Authorization: Bearer <access>`.
Errors always look like `{"error": {"code", "message", "details"}}`.

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register/` | sends 6-digit OTP |
| POST | `/auth/verify-email/` | `{email, code}` → tokens |
| POST | `/auth/resend-verification/` | |
| POST | `/auth/login/` | `{email, password}` → `{access, refresh, user}`; `email_not_verified` code if unverified |
| POST | `/auth/token/refresh/` | rotates the refresh token, blacklisting the old one |
| POST | `/auth/logout/` | `{refresh}` → blacklisted |
| GET/PATCH/DELETE | `/auth/me/` | DELETE needs `{password}` |
| POST | `/auth/change-password/` | revokes all tokens and returns new ones |
| POST | `/auth/password-reset/request/` · `/confirm/` | OTP-based |
| GET | `/places/search/?q=varanasi` | also accepts `City, State/Country` |
| GET | `/places/timezone/?lat=&lon=` | |
| CRUD | `/profiles/` | `place_id` **or** `latitude`+`longitude` (timezone is auto-resolved) |
| GET | `/profiles/{id}/chart/?vargas=D9,D10` | planets, lagna, houses, chalit, vargas, panchang, avakhada, dasha balance |
| GET | `/profiles/{id}/vargas/{D1..D60}/` | |
| GET | `/profiles/{id}/dashas/?depth=1..3` | MD/AD/PD tree |
| GET | `/profiles/{id}/dashas/drill/?path=Ra/Ve/Sa` | children of a period, down to prana |
| GET | `/profiles/{id}/dashas/current/?at=ISO` | running MD→Prana |
| GET | `/profiles/{id}/shadbala/` · `/bhavabala/` | |
| POST | `/vedic/panchang/` | `{place_id \| latitude,longitude, date?, time?, tz_name?}` |
| GET | `/profiles/{id}/strength-report/` | Shadbala/Bhava Bala with status, six sources and "what to do" |
| GET | `/daily/home/` | insight + why, current Mahā/Antar period, headline transit, today's windows |
| GET | `/daily/timeline/?date=` | Brahma muhurta, choghadiya (day & night), Rahu Kaal, Yamaganda, Gulika, Abhijit |
| GET | `/daily/panchang/?date=` | the day's panchang with kinds, Śaka year and an interpretation note |
| POST | `/daily/decision/` | `{activity, range}` → ranked windows with scores (Pro) |
| GET | `/daily/transits/` | gochara vs natal chart + Sade Sati |
| GET/PUT | `/remedies/goals/` | goal catalogue · set goals (`{goals:[...]}`: 1 on the free plan, up to 3 with Pro), which seeds remedies for them |
| GET/POST | `/remedies/` | list (seeded from goals, else the Daśā lord) / add for a graha or a custom remedy (Pro) |
| PATCH/DELETE | `/remedies/{id}/` | edit title/text/how/cadence/target/weekdays/reminder or `reset` (Pro) · remove (archived) |
| POST | `/remedies/{id}/progress/` | count / mark complete |
| GET | `/remedies/history/?days=365` | done vs due per day, for the heatmap |
| GET/PUT | `/journal/{date}/` · GET `/journal/trends/?days=7-90` | check-ins · mood with remedies done/due per day, timing and practice insights |
| GET/PATCH | `/alerts/prefs/` · GET `/alerts/schedule/?days=7` | preferences · upcoming notifications |
| GET | `/billing/` · POST `/billing/trial/` | plan status · start the free trial |

Daily endpoints use the user's active profile (`?profile=` overrides) and "where you live now"
(`current_place`, settable via `PATCH /auth/me/`; `?place_id=` overrides). The app registers with
email + password only; `user.needs_onboarding` stays true until the user has an active profile
(`POST /profiles/`) and goals (`PUT /remedies/goals/`). Registration still accepts optional
`current_place_id` and `profile`.

**Pro gating:** decision assistant, divisional charts other than D1, Dasha drill-down below
Antardaśā, more than one goal, adding and editing remedies (including reminders), and transit/Sade
Sati alerts (goal remedies, marking done, removing and the history heatmap are free). Grant Pro manually with
`python manage.py grant_pro user@example.com [--days N]` until store billing is integrated.

**Demo data:** `python manage.py seed_demo` creates `demo@example.com` / `Demo-pass-123` (verified,
onboarded, with chart, goal and remedies) plus 45 days of remedy completions and journal check-ins,
so the streak, heatmap and trends have something to show. Options: `--pro`, `--goals marriage,career`
(more than one needs `--pro`), `--days N`, `--email`, `--password`, `--seed N`, and `--reset` to replace
an existing demo account. `python manage.py seed_demo --clear` deletes **all** users and their data
(places stay); it asks for confirmation (`--noinput` skips it) and refuses unless `DEBUG=True`.

Timestamps are ISO-8601 with the profile's local UTC offset (e.g. `+05:30`).

## Calculation conventions

- **Positions**: Skyfield + JPL DE440s; geocentric, apparent, true ecliptic of date.
- **Ayanamsa**: Lahiri (Chitrapaksha), with IAU 2006 precession from the 1956 reference
  value and nutation applied (true ayanamsa). Registry in `engine/ayanamsa.py` for adding Raman/KP.
- **Nodes**: mean by default, true node per profile (`node_mode`).
- **Houses**: whole-sign for the rasi chart; Sripati bhavas for chalit and the strengths.
- **Panchang**: the Vedic day starts at sunrise (upper limb + refraction), so a birth before
  sunrise takes the previous weekday. Months are amanta, with adhika detection.
- **Dasha**: Vimshottari with a 365.2425-day year. Periods are generated lazily.
- **Shadbala**: BPHS / B.V. Raman. Chesta uses a heliocentric equivalent of the
  seeghrocha method; the Sun's chesta = ayana bala and the Moon's = paksha bala.
- **Bhava Bala**: adhipati + dig + drishti (Jupiter and Mercury counted in full), plus
  occupation (±60) and day/night sign adjustments.

Results are cached in `vedic.ComputedResult`, keyed by a hash of the birth data, the
options and `ENGINE_VERSION`. Editing a profile or bumping the version invalidates them.

## Production

- `DJANGO_SETTINGS_MODULE=astrology.settings.prod` (the default for wsgi/asgi). Set `SECRET_KEY`,
  `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` and email (below).
- **Email** goes through the Nitrosend REST API in production (`apps/core/mail.py`, no SMTP).
  Set `NITROSEND_API_KEY` (dashboard → Settings → API Keys) and `DEFAULT_FROM_EMAIL` to a
  verified sender identity in Nitrosend. `EMAIL_BACKEND` picks the sender: `console` (the dev
  default; codes print to the runserver console), `nitrosend`, or `smtp` (uses
  `EMAIL_HOST`/`EMAIL_PORT`/…). Set `EMAIL_BACKEND=nitrosend` locally to send real emails.
- `python manage.py collectstatic && gunicorn astrology.wsgi -w 4 -b 0.0.0.0:8000`
- `python manage.py check --deploy --settings=astrology.settings.prod` should report no issues.
- Run `download_ephemeris` and `load_places` during provisioning. Both are idempotent.
- Moving to Postgres or Redis later is just `DATABASE_URL` / `CACHE_URL`. Use Redis for
  `CACHE_URL` once you run more than one worker, so rate limits are shared.
