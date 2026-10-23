"""Mood trends linked to timing (Chandrabala, weekday, paksha) and to remedy practice."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from statistics import mean
from zoneinfo import ZoneInfo

import numpy as np

from apps.remedies import services as remedies
from apps.vedic.content.common import WEEKDAY, pick
from apps.vedic.engine import ephemeris as ephem
from apps.vedic.engine.transits import _lons

from .models import JournalEntry

GOOD_FROM_MOON = {1, 3, 6, 7, 10, 11}
DEFAULT_TAGS = {"en": ["Work", "Family", "Health", "Rest"], "hi": ["काम", "परिवार", "स्वास्थ्य", "विश्राम"]}
MIN_ENTRIES = 5
MIN_DIFF = 0.4
MIN_PRACTICE_DAYS = 3  # logged days needed on each side (practised / skipped) for the practice insight


def practice_insight(history: list, done_due: dict, lang: str) -> dict | None:
    """Mood on days with remedies done vs days they were due but skipped — shown only when practice
    days are clearly brighter, so a thin or noisy sample never makes a claim."""
    practised, skipped = [], []
    for e in history:
        done, due = done_due.get(e.date, (0, 0))
        if done:
            practised.append(e.rating)
        elif due:
            skipped.append(e.rating)
    if len(practised) < MIN_PRACTICE_DAYS or len(skipped) < MIN_PRACTICE_DAYS:
        return None
    on, off = mean(practised), mean(skipped)
    if on - off < MIN_DIFF:
        return None
    return {"kind": "good", "glyph": "✦", "text": pick(
        lang,
        f"On days you do your remedies, your mood averages **{on:.1f}** vs **{off:.1f}** on days you skip them.",
        f"जिन दिनों आप उपाय करते हैं, आपका मन औसतन **{on:.1f}** रहता है, और जिन दिनों छोड़ते हैं उन दिनों **{off:.1f}**।")}


def trends(user, today: date, days: int, lang: str, natal_moon_sign: int | None, tz: ZoneInfo) -> dict:
    start = today - timedelta(days=days - 1)
    entries = {e.date: e for e in JournalEntry.objects.filter(user=user, date__gte=start, date__lte=today)}
    # Remedies done vs due per day (archived remedies included), over the longer pattern window.
    window = max(days, 120)
    done_due = {date.fromisoformat(d["date"]): (d["done"], d["due"])
                for d in remedies.history(user, today, window)["days"]}
    bars = []
    for i in range(days):
        d = start + timedelta(days=i)
        done, due = done_due.get(d, (0, 0))
        bars.append({"date": d.isoformat(), "rating": entries[d].rating if d in entries else None,
                     "remedies": {"done": done, "due": due}})
    ratings = [e.rating for e in entries.values()]
    insights = []

    # Use a longer history for patterns than for the chart.
    history = list(JournalEntry.objects.filter(user=user, date__lte=today, date__gte=today - timedelta(days=window)))
    practice = practice_insight(history, done_due, lang)
    if practice:
        insights.append(practice)
    if len(history) >= MIN_ENTRIES:
        overall = mean(e.rating for e in history)
        noons = np.array([ephem.to_time(datetime.combine(e.date, time(12), tzinfo=tz)).tt for e in history])
        moon = _lons("Mo", noons)
        sun = _lons("Su", noons)

        if natal_moon_sign is not None:
            good = [e.rating for e, m in zip(history, moon) if ((int(m // 30) - natal_moon_sign) % 12 + 1) in GOOD_FROM_MOON]
            bad = [e.rating for e, m in zip(history, moon) if ((int(m // 30) - natal_moon_sign) % 12 + 1) not in GOOD_FROM_MOON]
            if len(good) >= 2 and len(bad) >= 2 and mean(good) - mean(bad) >= MIN_DIFF:
                pct = round((mean(good) - mean(bad)) / mean(bad) * 100)
                insights.append({"kind": "good", "glyph": "↑", "text": pick(
                    lang,
                    f"Your brighter days cluster when the **Moon passes supportive houses** from your birth Moon — about {pct}% higher.",
                    f"आपके अच्छे दिन तब अधिक होते हैं जब **चंद्रमा जन्म चंद्र से शुभ भावों** में होता है — लगभग {pct}% बेहतर।")})

        by_day: dict[int, list[int]] = {}
        for e in history:
            by_day.setdefault((e.date.weekday() + 1) % 7, []).append(e.rating)
        candidates = [(mean(v), d) for d, v in by_day.items() if len(v) >= 2]
        if candidates:
            low, d = min(candidates)
            if overall - low >= MIN_DIFF:
                name = WEEKDAY[lang][d]
                insights.append({"kind": "neutral", "glyph": "◐", "text": pick(
                    lang, f"**{name}s** trend a little lower. Plan them lightly.",
                    f"**{name}** को मन कुछ भारी रहता है। उस दिन योजनाएँ हल्की रखें।")})

        shukla = [e.rating for e, m, s in zip(history, moon, sun) if (m - s) % 360 < 180]
        krishna = [e.rating for e, m, s in zip(history, moon, sun) if (m - s) % 360 >= 180]
        if len(insights) < 2 and len(shukla) >= 2 and len(krishna) >= 2 and abs(mean(shukla) - mean(krishna)) >= MIN_DIFF:
            waxing = mean(shukla) > mean(krishna)
            insights.append({"kind": "good" if waxing else "neutral", "glyph": "☽", "text": pick(
                lang,
                f"You feel lighter in the **{'waxing (Shukla)' if waxing else 'waning (Krishna)'}** fortnight.",
                f"**{'शुक्ल' if waxing else 'कृष्ण'} पक्ष** में आपका मन अधिक हल्का रहता है।")})
        if not insights:
            avg = round(overall, 1)
            insights.append({"kind": "neutral", "glyph": "◑", "text": pick(
                lang, f"No strong pattern yet — your days have held **steady around {avg}**. Keep checking in.",
                f"अभी कोई स्पष्ट पैटर्न नहीं — आपके दिन **लगभग {avg}** पर स्थिर रहे हैं। लिखते रहें।")})
    else:
        insights.append({"kind": "neutral", "glyph": "◌", "text": pick(
            lang, f"Keep logging — patterns appear after {MIN_ENTRIES} check-ins.",
            f"लिखते रहें — {MIN_ENTRIES} प्रविष्टियों के बाद पैटर्न दिखने लगेंगे।")})

    return {"days": days, "bars": bars, "average": round(mean(ratings), 1) if ratings else None,
            "count": len(ratings), "insights": insights[:2]}
