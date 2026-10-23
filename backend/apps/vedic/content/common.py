"""Shared bilingual vocabulary (en / hi) for generated texts."""

LANGS = ("en", "hi")

GLYPH = {"Su": "☉", "Mo": "☽", "Ma": "♂", "Me": "☿", "Ju": "♃", "Ve": "♀", "Sa": "♄", "Ra": "☊", "Ke": "☋"}

# Everyday Hinglish spelling, as typed in messages.
SANSKRIT = {"Su": "Surya", "Mo": "Chandra", "Ma": "Mangal", "Me": "Budh", "Ju": "Guru",
            "Ve": "Shukra", "Sa": "Shani", "Ra": "Rahu", "Ke": "Ketu"}
ENGLISH = {"Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury", "Ju": "Jupiter",
           "Ve": "Venus", "Sa": "Saturn", "Ra": "North node", "Ke": "South node"}
HINDI = {"Su": "सूर्य", "Mo": "चंद्र", "Ma": "मंगल", "Me": "बुध", "Ju": "गुरु",
         "Ve": "शुक्र", "Sa": "शनि", "Ra": "राहु", "Ke": "केतु"}


def short(code: str, lang: str) -> str:
    """Primary name: "Budh" / "बुध"."""
    return HINDI[code] if lang == "hi" else SANSKRIT[code]


def full(code: str, lang: str) -> str:
    """"Budh · Mercury" / "बुध"."""
    return HINDI[code] if lang == "hi" else f"{SANSKRIT[code]} · {ENGLISH[code]}"


def english(code: str, lang: str) -> str:
    return HINDI[code] if lang == "hi" else ENGLISH[code]


_EN_ORD = {1: "st", 2: "nd", 3: "rd"}
_HI_ORD = ["पहले", "दूसरे", "तीसरे", "चौथे", "पाँचवें", "छठे", "सातवें", "आठवें", "नौवें", "दसवें", "ग्यारहवें", "बारहवें"]


def ordinal(n: int, lang: str) -> str:
    if lang == "hi":
        return _HI_ORD[n - 1]
    suffix = "th" if 10 <= n % 100 <= 20 else _EN_ORD.get(n % 10, "th")
    return f"{n}{suffix}"


KARAKA = {
    "en": ["Lagna", "Dhan", "Sahaj", "Sukh", "Putra", "Ari", "Yuvati", "Randhra", "Dharma", "Karma", "Labh", "Vyay"],
    "hi": ["लग्न", "धन", "सहज", "सुख", "पुत्र", "अरि", "युवती", "रंध्र", "धर्म", "कर्म", "लाभ", "व्यय"],
}
HOUSE_MEANING = {
    "en": ["self, body, vitality", "wealth, speech, family", "courage, siblings, effort",
           "home, mother, inner peace", "creativity, children, mind", "health, service, debts",
           "partnership & contracts", "depth, change, the hidden", "fortune, belief, father",
           "career, status, action", "gains, friends, networks", "release, rest, moksha"],
    "hi": ["स्वयं, शरीर, ऊर्जा", "धन, वाणी, परिवार", "साहस, भाई-बहन, प्रयास",
           "घर, माता, मन की शांति", "रचनात्मकता, संतान, बुद्धि", "स्वास्थ्य, सेवा, ऋण",
           "साझेदारी और अनुबंध", "गहराई, परिवर्तन, गूढ़ बातें", "भाग्य, आस्था, पिता",
           "करियर, प्रतिष्ठा, कर्म", "लाभ, मित्र, संपर्क", "मुक्ति, विश्राम, मोक्ष"],
}

WEEKDAY = {
    "en": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "hi": ["रविवार", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार"],
}
WEEKDAY_SHORT = {
    "en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "hi": ["रवि", "सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि"],
}
# Planet -> its weekday index (0 = Sunday)
PLANET_DAY = {"Su": 0, "Mo": 1, "Ma": 2, "Me": 3, "Ju": 4, "Ve": 5, "Sa": 6, "Ra": 6, "Ke": 2}

KIND_LABEL = {
    "en": {"good": "Auspicious", "neutral": "Neutral", "bad": "Avoid"},
    "hi": {"good": "शुभ", "neutral": "सामान्य", "bad": "टालें"},
}


def pick(lang: str, en: str, hi: str) -> str:
    return hi if lang == "hi" else en


def norm_lang(value: str | None) -> str:
    return "hi" if (value or "").lower().startswith("hi") else "en"


NAKSHATRA_HI = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा",
    "मघा", "पूर्व फाल्गुनी", "उत्तर फाल्गुनी", "हस्त", "चित्रा", "स्वाति", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्व भाद्रपद", "उत्तर भाद्रपद", "रेवती",
]
YOGA_HI = [
    "विष्कुम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन", "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड",
    "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव", "सिद्ध",
    "साध्य", "शुभ", "शुक्ल", "ब्रह्म", "इन्द्र", "वैधृति",
]


def nakshatra_name(index: int, en_name: str, lang: str) -> str:
    """index 1..27."""
    return NAKSHATRA_HI[index - 1] if lang == "hi" else en_name


def yoga_name(index: int, en_name: str, lang: str) -> str:
    return YOGA_HI[index - 1] if lang == "hi" else en_name
