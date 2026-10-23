"""Activities for the decision assistant and the phrases used to explain scores."""
from .common import HINDI, SANSKRIT, WEEKDAY, ordinal

GOOD_NAK = {  # nakshatra indexes 1..27
    "travel": {1, 5, 7, 8, 13, 17, 22, 23, 27},
    "purchase": {1, 4, 5, 7, 8, 12, 13, 14, 15, 17, 21, 22, 23, 26, 27},
    "contract": {4, 8, 12, 13, 17, 21, 22, 26, 27},
    "venture": {1, 4, 7, 8, 12, 13, 14, 17, 21, 22, 26, 27},
    "medical": {1, 5, 7, 8, 13, 14, 15, 17, 22, 27},
}
BAD_NAK = {2, 6, 9, 10, 11, 18, 19, 20, 25}  # ugra + tikshna
GOOD_DAYS = {"travel": {1, 3, 4, 5}, "purchase": {1, 3, 4, 5}, "contract": {3, 4, 5},
             "venture": {0, 3, 4, 5}, "medical": {1, 3, 4, 5}}
BAD_DAYS = {"travel": {0, 2, 6}, "purchase": {2, 6}, "contract": {2}, "venture": {2, 6}, "medical": {2}}
KEY_PLANET = {"purchase": "Ve", "contract": "Me", "venture": "Ju"}
WINDOW_BONUS = {"travel": "choghadiya.char", "purchase": "choghadiya.labh", "venture": "choghadiya.labh"}

ACTIVITIES = {
    "travel": ("Travel", "travel", "✈", "यात्रा", "यात्रा"),
    "purchase": ("Purchase", "a purchase", "◈", "ख़रीद", "ख़रीदारी"),
    "contract": ("Contract", "a contract", "✎", "अनुबंध", "अनुबंध"),
    "venture": ("New venture", "a new venture", "❋", "नया उपक्रम", "नया उपक्रम"),
    "medical": ("Medical", "a procedure", "✚", "चिकित्सा", "चिकित्सा प्रक्रिया"),
}
RANGES = {"today": ("Today", "आज", 1), "week": ("Next 7 days", "अगले 7 दिन", 7), "month": ("This month", "इस महीने", 30)}

TARA = ["Janma", "Sampat", "Vipat", "Kshema", "Pratyak", "Sadhana", "Naidhana", "Mitra", "Param Mitra"]
TARA_HI = ["जन्म", "संपत", "विपत", "क्षेम", "प्रत्यक", "साधना", "नैधन", "मित्र", "परम मित्र"]
TARA_SCORE = [-4, 9, -12, 8, -10, 9, -16, 8, 10]


def activity_meta(key: str, lang: str) -> dict:
    en, en_obj, glyph, hi, hi_obj = ACTIVITIES[key]
    return {"key": key, "label": hi if lang == "hi" else en, "object": hi_obj if lang == "hi" else en_obj,
            "glyph": glyph}


def factor_phrase(factor: str, lang: str, **kw) -> str:
    hi = lang == "hi"
    if factor == "window":
        return kw["name"]
    if factor == "tara":
        i = kw["tara"]
        return (f"{TARA_HI[i]} तारा" if hi else f"{TARA[i]} tara from your birth star")
    if factor == "chandra":
        h = kw["house"]
        good = kw["good"]
        if hi:
            return f"चंद्र आपके जन्म चंद्र से {ordinal(h, 'hi')} भाव में" + ("" if good else " (प्रतिकूल)")
        return f"Moon {ordinal(h, 'en')} from your birth Moon" + ("" if good else " (unfavourable)")
    if factor == "tithi":
        return ("रिक्ता/अमावस्या तिथि" if hi else "a Rikta or Amavasya tithi") if kw["bad"] else \
               ("शुभ तिथि" if hi else "a supportive tithi")
    if factor == "nakshatra":
        name = kw["name"]
        return (f"{name} नक्षत्र अनुकूल" if hi else f"{name} suits it") if kw["good"] else \
               (f"{name} नक्षत्र प्रतिकूल" if hi else f"{name} works against it")
    if factor == "weekday":
        day = WEEKDAY[lang][kw["weekday"]]
        return (f"{day} अनुकूल" if hi else f"{day} favours it") if kw["good"] else \
               (f"{day} कमज़ोर करता है" if hi else f"{day} weakens it")
    if factor == "retro":
        p = kw["planet"]
        return f"{HINDI[p]} वक्री" if hi else f"{SANSKRIT[p]} still retrograde"
    if factor == "kaal":
        return kw["name"] + (" से टकराव — टालें" if hi else " overlaps — avoid")
    return ""


def join_reason(parts: list[str], lang: str) -> str:
    if not parts:
        return ""
    if lang == "hi":
        return "; ".join(parts) + "।"
    s = " + ".join(parts[:2]) if len(parts) > 1 else parts[0]
    return s[0].upper() + s[1:] + "."
