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


# Notification wording for a period: key -> (en name, en advice, hi name, hi advice).
# Advice opens with "Suitable for" or "Avoid" so the tone is clear from the shade.
_ALERTS = {
    "choghadiya.amrit": ("Amrit period", "Suitable for important beginnings: sign, commit, launch.",
                         "अमृत चौघड़िया", "महत्वपूर्ण शुरुआत के लिए उत्तम: हस्ताक्षर, संकल्प, आरंभ।"),
    "choghadiya.shubh": ("Shubh period", "Suitable for ceremonies, learning and auspicious work.",
                         "शुभ चौघड़िया", "अनुष्ठान, अध्ययन और शुभ कार्यों के लिए उपयुक्त।"),
    "choghadiya.labh": ("Labh period", "Suitable for business, trade and money matters.",
                        "लाभ चौघड़िया", "व्यापार, लेन-देन और धन से जुड़े कामों के लिए उपयुक्त।"),
    "choghadiya.char": ("Char period", "Suitable for travel, errands and anything on the move.",
                        "चर चौघड़िया", "यात्रा, भाग-दौड़ और चलते-फिरते कामों के लिए उपयुक्त।"),
    "choghadiya.udveg": ("Udveg period", "Avoid big decisions and confrontations; keep to routine work.",
                         "उद्वेग चौघड़िया", "बड़े निर्णय और विवाद टालें; नियमित काम करें।"),
    "choghadiya.kaal": ("Kaal period", "Avoid new starts and big purchases; finish pending work instead.",
                        "काल चौघड़िया", "नई शुरुआत और बड़ी खरीदारी टालें; अधूरे काम पूरे करें।"),
    "choghadiya.rog": ("Rog period", "Avoid medical procedures, disputes and sensitive conversations.",
                       "रोग चौघड़िया", "चिकित्सा प्रक्रियाएँ, विवाद और संवेदनशील बातचीत टालें।"),
    "rahu_kaal": ("Rahu Kaal", "Avoid new ventures, setting out on journeys and big commitments.",
                  "राहु काल", "नए उद्यम, यात्रा की शुरुआत और बड़े संकल्प टालें।"),
}


def alert_text(key: str, lang: str) -> dict:
    v = _ALERTS[key]
    o = 2 if lang == "hi" else 0
    return {"name": v[o], "advice": v[o + 1]}
