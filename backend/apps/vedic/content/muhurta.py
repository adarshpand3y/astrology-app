"""Names and glosses for daily timing periods."""

# key -> (en name, en short gloss, en long gloss, hi name, hi short gloss, hi long gloss)
_PERIODS = {
    "rahu_kaal": ("Rahu Kaal", "avoid new starts", "Avoid launching anything new",
                  "राहु काल", "नई शुरुआत टालें", "कोई भी नया काम शुरू न करें"),
    "yamaganda": ("Yamaganda", "obstruction period", "Obstruction period — defer decisions",
                  "यमगंड", "बाधा काल", "बाधा का समय — निर्णय टालें"),
    "gulika": ("Gulika Kaal", "routine only", "Recurs on itself — routine only",
               "गुलिक काल", "केवल नियमित काम", "जो होता है वह दोहराता है — केवल नियमित कार्य"),
    "abhijit": ("Abhijit Muhurat", "midday victory hour", "Midday victory hour — most auspicious",
                "अभिजित मुहूर्त", "मध्याह्न विजय मुहूर्त", "मध्याह्न का विजय मुहूर्त — सबसे शुभ"),
    "abhijit_wed": ("Abhijit Muhurat", "not used on Wednesdays", "Traditionally avoided on Wednesdays",
                    "अभिजित मुहूर्त", "बुधवार को वर्जित", "परंपरा से बुधवार को नहीं लिया जाता"),
    "brahma": ("Brahma Muhurat", "before dawn", "Before dawn — meditation & study",
               "ब्रह्म मुहूर्त", "भोर से पहले", "भोर से पहले — ध्यान और अध्ययन"),
    "choghadiya.amrit": ("Amrit Choghadiya", "nectar window", "Nectar window — sign, commit, begin",
                         "अमृत चौघड़िया", "अमृत काल", "अमृत समय — हस्ताक्षर, संकल्प, आरंभ"),
    "choghadiya.shubh": ("Shubh Choghadiya", "auspicious", "Auspicious — ceremonies & learning",
                         "शुभ चौघड़िया", "शुभ समय", "शुभ — अनुष्ठान और अध्ययन"),
    "choghadiya.labh": ("Labh Choghadiya", "gain", "Gain — business, trade & money",
                        "लाभ चौघड़िया", "लाभ", "लाभ — व्यापार और धन के काम"),
    "choghadiya.char": ("Char Choghadiya", "movable", "Movable — good for travel & errands",
                        "चर चौघड़िया", "चर", "चर — यात्रा और भाग-दौड़ के लिए अच्छा"),
    "choghadiya.udveg": ("Udveg Choghadiya", "anxiety", "Anxiety — keep important work aside",
                         "उद्वेग चौघड़िया", "उद्वेग", "उद्वेग — महत्वपूर्ण काम अलग रखें"),
    "choghadiya.kaal": ("Kaal Choghadiya", "loss", "Loss — postpone new starts",
                        "काल चौघड़िया", "काल", "हानि — नई शुरुआत टालें"),
    "choghadiya.rog": ("Rog Choghadiya", "illness", "Illness period — hold sensitive matters",
                       "रोग चौघड़िया", "रोग", "रोग का समय — संवेदनशील मामले रोकें"),
    "sunrise": ("Sunrise", "the day opens", "The Vedic day begins",
                "सूर्योदय", "दिन का आरंभ", "वैदिक दिन का आरंभ"),
    "sunset": ("Sunset", "sandhya", "Sandhya — reflection & closing",
               "सूर्यास्त", "संध्या", "संध्या — चिंतन और समापन"),
}


def period_text(key: str, lang: str) -> dict:
    v = _PERIODS[key]
    o = 3 if lang == "hi" else 0
    return {"name": v[o], "short": v[o + 1], "gloss": v[o + 2]}
