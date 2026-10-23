"""Panchang interpretation: kinds (good/neutral/bad), glosses and notes."""
from .common import HINDI, SANSKRIT, ordinal, pick

GOOD, NEUTRAL, BAD = "good", "neutral", "bad"

# --- Tithi --------------------------------------------------------------------------
def tithi_kind(index: int) -> str:
    """index 1..30."""
    n = (index - 1) % 15 + 1
    if index == 30 or n in (4, 9, 14):  # Amavasya and Rikta tithis
        return BAD
    if n == 8:
        return NEUTRAL
    return GOOD


def tithi_detail(index: int, lang: str) -> str:
    n = (index - 1) % 15 + 1
    shukla = index <= 15
    if lang == "hi":
        return f"{n}वीं · {'शुक्ल पक्ष' if shukla else 'कृष्ण पक्ष'}"
    return f"{ordinal(n, 'en')} · {'waxing' if shukla else 'waning'}"


# --- Vara ---------------------------------------------------------------------------
_VARA = [  # (lord, kind, en theme, hi theme)
    ("Su", NEUTRAL, "vitality", "ऊर्जा"), ("Mo", GOOD, "care", "भावना"), ("Ma", NEUTRAL, "courage", "साहस"),
    ("Me", GOOD, "intellect", "बुद्धि"), ("Ju", GOOD, "wisdom", "ज्ञान"), ("Ve", GOOD, "harmony", "सामंजस्य"),
    ("Sa", NEUTRAL, "discipline", "अनुशासन"),
]


def vara_info(weekday: int, lang: str) -> dict:
    lord, kind, en, hi = _VARA[weekday]
    name = HINDI[lord] if lang == "hi" else SANSKRIT[lord]
    return {"kind": kind, "detail": f"{name} · {pick(lang, en, hi)}"}


# --- Nakshatra ----------------------------------------------------------------------
NAK_NATURE = {  # nakshatra index (1..27) -> nature
    4: "dhruva", 12: "dhruva", 21: "dhruva", 26: "dhruva",
    7: "chara", 15: "chara", 22: "chara", 23: "chara", 24: "chara",
    2: "ugra", 10: "ugra", 11: "ugra", 20: "ugra", 25: "ugra",
    3: "mishra", 16: "mishra",
    1: "laghu", 8: "laghu", 13: "laghu",
    5: "mridu", 14: "mridu", 17: "mridu", 27: "mridu",
    6: "tikshna", 9: "tikshna", 18: "tikshna", 19: "tikshna",
}
NATURE_KIND = {"dhruva": GOOD, "chara": GOOD, "laghu": GOOD, "mridu": GOOD, "mishra": NEUTRAL,
               "ugra": BAD, "tikshna": BAD}
# nature -> (en favours, en good for, en poor for, hi favours, hi good for, hi poor for)
NATURE_TEXT = {
    "dhruva": ("steady, lasting work", "foundations and long commitments", "hasty change",
               "स्थिर, टिकाऊ काम", "नींव और लंबे संकल्प", "जल्दबाज़ी के बदलाव"),
    "chara": ("movement and change", "travel and new routines", "locking things in",
              "गति और परिवर्तन", "यात्रा और नई दिनचर्या", "बातों को स्थायी करना"),
    "laghu": ("quick, light tasks", "trade, learning and healing", "heavy undertakings",
              "तेज़, हल्के काम", "व्यापार, अध्ययन और उपचार", "भारी उपक्रम"),
    "mridu": ("gentle, relationship-minded effort", "repair and friendship", "confrontation",
              "कोमल, संबंध-केंद्रित प्रयास", "सुधार और मित्रता", "टकराव"),
    "mishra": ("mixed, everyday tasks", "routine work", "major launches",
               "मिश्रित, रोज़मर्रा के काम", "नियमित काम", "बड़ी शुरुआत"),
    "ugra": ("bold, decisive effort", "competition and hard tasks", "gentle beginnings",
             "साहसी, निर्णायक प्रयास", "प्रतियोगिता और कठिन काम", "कोमल शुरुआत"),
    "tikshna": ("cutting away and endings", "clearing and closure", "new ventures",
                "काट-छाँट और समापन", "सफ़ाई और समापन", "नए उपक्रम"),
}


def nakshatra_info(index: int, lord: str, lang: str) -> dict:
    nature = NAK_NATURE[index]
    name = HINDI[lord] if lang == "hi" else SANSKRIT[lord]
    return {"kind": NATURE_KIND[nature], "nature": nature,
            "detail": pick(lang, f"ruled by {name}", f"स्वामी {name}")}


# --- Yoga ---------------------------------------------------------------------------
BAD_YOGAS = {1, 6, 9, 10, 13, 15, 17, 19, 27}
_YOGA_GLOSS = [
    ("obstacles to clear", "बाधाएँ हटाने का"), ("affection", "स्नेह"), ("longevity", "दीर्घायु"),
    ("good fortune", "सौभाग्य"), ("splendour", "शोभा"), ("danger · care", "संकट · सावधानी"),
    ("good deeds", "सत्कर्म"), ("steadiness", "धैर्य"), ("sharp pain · care", "पीड़ा · सावधानी"),
    ("knots · care", "उलझन · सावधानी"), ("growth", "वृद्धि"), ("permanence", "स्थिरता"),
    ("setbacks · care", "आघात · सावधानी"), ("joy", "हर्ष"), ("force · care", "कठोरता · सावधानी"),
    ("success", "सिद्धि"), ("calamity · care", "विपत्ति · सावधानी"), ("comfort", "सुख-सुविधा"),
    ("barriers · care", "रुकावट · सावधानी"), ("auspicious", "मंगलमय"), ("accomplishment", "सफलता"),
    ("achievable aims", "साध्य लक्ष्य"), ("blessings", "शुभता"), ("clarity & resolve", "स्पष्टता और संकल्प"),
    ("knowledge", "ज्ञान"), ("leadership", "नेतृत्व"), ("division · care", "विभाजन · सावधानी"),
]


def yoga_info(index: int, lang: str) -> dict:
    en, hi = _YOGA_GLOSS[index - 1]
    return {"kind": BAD if index in BAD_YOGAS else GOOD, "detail": pick(lang, en, hi)}


# --- Karana -------------------------------------------------------------------------
_KARANA = {
    "Bava": (GOOD, "growth", "वृद्धि"), "Balava": (GOOD, "strength", "बल"), "Kaulava": (GOOD, "friendship", "मैत्री"),
    "Taitila": (NEUTRAL, "steady effort", "स्थिर प्रयास"), "Gara": (GOOD, "work & home", "काम और घर"),
    "Vanija": (GOOD, "trade", "व्यापार"), "Vishti": (BAD, "Bhadra · avoid starts", "भद्रा · शुरुआत टालें"),
    "Shakuni": (NEUTRAL, "strategy", "रणनीति"), "Chatushpada": (NEUTRAL, "livestock & land", "पशु और भूमि"),
    "Naga": (NEUTRAL, "hidden forces", "छिपी शक्तियाँ"), "Kimstughna": (GOOD, "a fresh start", "नई शुरुआत"),
}


def karana_info(name: str, lang: str) -> dict:
    kind, en, hi = _KARANA.get(name, (NEUTRAL, "", ""))
    return {"kind": kind, "detail": pick(lang, en, hi)}


# --- Calendar -------------------------------------------------------------------------
def shaka_year(gregorian_year: int, month: int, amanta_month: str) -> int:
    """Shaka Samvat changes at Chaitra Shukla Pratipada (Mar/Apr)."""
    early = month <= 4 and amanta_month in ("Margashirsha", "Pausha", "Magha", "Phalguna")
    return gregorian_year - (79 if early else 78)


def note(yoga_name: str, yoga_kind: str, nak_name: str, nature: str, lang: str) -> str:
    t = NATURE_TEXT[nature]
    if lang == "hi":
        tone = "सहायक" if yoga_kind == GOOD else "चुनौतीपूर्ण"
        return (f"{nak_name} नक्षत्र पर {tone} {yoga_name} योग {t[3]} के अनुकूल है। "
                f"{t[4]} के लिए अच्छा, {t[5]} के लिए नहीं।")
    article = "An" if yoga_name[:1].upper() in "AEIOU" else "A"
    tone = "" if yoga_kind == GOOD else " (testing)"
    return (f"{article} {yoga_name}{tone} yoga on {nak_name} favours {t[0]}. "
            f"Good for {t[1]}, poor for {t[2]}.")
