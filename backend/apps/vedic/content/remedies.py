"""Remedy catalogue: mantra, fasting, charity and gemstone for each graha."""
from .common import HINDI, SANSKRIT, WEEKDAY, PLANET_DAY

KINDS = ("mantra", "fast", "charity", "gem")
KIND_GLYPH = {"mantra": "ॐ", "fast": "◐", "charity": "❋", "gem": "◆"}
KIND_LABEL = {"en": {"mantra": "Mantra", "fast": "Fasting", "charity": "Charity", "gem": "Gemstone"},
              "hi": {"mantra": "मंत्र", "fast": "व्रत", "charity": "दान", "gem": "रत्न"}}
MANTRA_TARGET = 108

# planet -> mantra (en text, hi text), charity (en, hi), gem (en, hi, finger en, finger hi)
_DATA = {
    "Su": {"mantra": ("Om Hraam Hreem Hraum Sah Suryaya Namah", "ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः"),
           "charity": ("Wheat or jaggery", "गेहूँ या गुड़"),
           "gem": ("Ruby · Manik", "माणिक्य", "ring finger", "अनामिका")},
    "Mo": {"mantra": ("Om Shraam Shreem Shraum Sah Chandramase Namah", "ॐ श्रां श्रीं श्रौं सः चन्द्रमसे नमः"),
           "charity": ("Rice, milk or white cloth", "चावल, दूध या सफ़ेद वस्त्र"),
           "gem": ("Pearl · Moti", "मोती", "little finger", "कनिष्ठा")},
    "Ma": {"mantra": ("Om Kraam Kreem Kraum Sah Bhaumaya Namah", "ॐ क्रां क्रीं क्रौं सः भौमाय नमः"),
           "charity": ("Red lentils (masoor)", "मसूर दाल"),
           "gem": ("Red coral · Moonga", "मूँगा", "ring finger", "अनामिका")},
    "Me": {"mantra": ("Om Braam Breem Braum Sah Budhaya Namah", "ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः"),
           "charity": ("Green gram (moong)", "हरी मूँग"),
           "gem": ("Emerald · Panna", "पन्ना", "little finger", "कनिष्ठा")},
    "Ju": {"mantra": ("Om Graam Greem Graum Sah Gurave Namah", "ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः"),
           "charity": ("Turmeric or chana dal", "हल्दी या चना दाल"),
           "gem": ("Yellow sapphire · Pukhraj", "पुखराज", "index finger", "तर्जनी")},
    "Ve": {"mantra": ("Om Draam Dreem Draum Sah Shukraya Namah", "ॐ द्रां द्रीं द्रौं सः शुक्राय नमः"),
           "charity": ("White sweets or curd", "सफ़ेद मिठाई या दही"),
           "gem": ("Diamond or white sapphire", "हीरा या सफ़ेद पुखराज", "middle finger", "मध्यमा")},
    "Sa": {"mantra": ("Om Praam Preem Praum Sah Shanaye Namah", "ॐ प्रां प्रीं प्रौं सः शनये नमः"),
           "charity": ("Black sesame or mustard oil", "काले तिल या सरसों का तेल"),
           "gem": ("Blue sapphire · Neelam", "नीलम", "middle finger", "मध्यमा")},
    "Ra": {"mantra": ("Om Bhraam Bhreem Bhraum Sah Rahave Namah", "ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः"),
           "charity": ("Blankets or black gram", "कंबल या उड़द"),
           "gem": ("Hessonite · Gomed", "गोमेद", "middle finger", "मध्यमा")},
    "Ke": {"mantra": ("Om Sraam Sreem Sraum Sah Ketave Namah", "ॐ स्रां स्रीं स्रौं सः केतवे नमः"),
           "charity": ("Sesame or a multi-coloured cloth", "तिल या बहुरंगी वस्त्र"),
           "gem": ("Cat's eye · Lehsunia", "लहसुनिया", "ring finger", "अनामिका")},
}

_DOMAIN = {
    "Su": ("confidence, vitality and recognition", "आत्मविश्वास, ऊर्जा और पहचान"),
    "Mo": ("mind, sleep and emotional steadiness", "मन, नींद और भावनात्मक स्थिरता"),
    "Ma": ("courage, energy and drive", "साहस, ऊर्जा और उत्साह"),
    "Me": ("clarity of thought, speech and timing", "विचारों की स्पष्टता, वाणी और समय की समझ"),
    "Ju": ("wisdom, faith and growth", "ज्ञान, आस्था और विकास"),
    "Ve": ("relationships, comfort and joy", "संबंध, सुख और आनंद"),
    "Sa": ("patience, discipline and endurance", "धैर्य, अनुशासन और सहनशक्ति"),
    "Ra": ("ambition and clarity amid confusion", "महत्वाकांक्षा और भ्रम में स्पष्टता"),
    "Ke": ("detachment and inner insight", "वैराग्य और अंतर्दृष्टि"),
}


def remedy(planet: str, kind: str, lang: str) -> dict:
    """Display data for one remedy (title, cadence, how & why...)."""
    hi = lang == "hi"
    d = _DATA[planet]
    day = WEEKDAY[lang][PLANET_DAY[planet]]
    name = HINDI[planet] if hi else SANSKRIT[planet]
    domain = _DOMAIN[planet][1 if hi else 0]
    if kind == "mantra":
        return {
            "title": f"{name} बीज मंत्र" if hi else f"{name} beej mantra",
            "cadence": "108 बार · हर सुबह" if hi else "108× · every morning",
            "text": d["mantra"][1 if hi else 0],
            "how": (f"सूर्योदय के बाद के एक घंटे में पूर्व की ओर मुख करके 108 बार जप करें। यह {name} को बल देता है — {domain}। माला से गिनती रखना आसान होता है।"
                    if hi else f"Recite 108 times facing east, ideally within the hour after sunrise. Strengthens {name} — {domain}. A mala helps you keep count."),
            "target": MANTRA_TARGET, "weekday": None,
        }
    if kind == "fast":
        return {
            "title": f"{day} व्रत" if hi else f"{day} fast",
            "cadence": f"साप्ताहिक · {name} का दिन" if hi else f"weekly · {name} day",
            "text": "",
            "how": (f"{day} को एक समय सादा भोजन करें या फलाहार रखें। व्रत {name} के दिन मन को अनुशासित करता है — {domain}।"
                    if hi else f"Keep a simple one-meal or fruit fast on {day}s. Fasting on {name}'s day steadies {domain}."),
            "target": 1, "weekday": PLANET_DAY[planet],
        }
    if kind == "charity":
        item = d["charity"][1 if hi else 0]
        return {
            "title": item, "cadence": f"{day}" if hi else f"{day}s",
            "text": "",
            "how": (f"{day} को ज़रूरतमंद को {item} दान करें। निःस्वार्थ दान {name} के कठिन प्रभाव को नरम करता है।"
                    if hi else f"Give {item.lower()} to someone in need on {day}s. Giving without expectation softens {name}'s harder edges."),
            "target": 1, "weekday": PLANET_DAY[planet],
        }
    en_gem, hi_gem, finger_en, finger_hi = d["gem"]
    return {
        "title": hi_gem if hi else en_gem,
        "cadence": f"धारण · दाहिने हाथ की {finger_hi}" if hi else f"wear · right {finger_en}",
        "text": "",
        "how": ("रत्न शक्तिशाली होते हैं और ग्रह के अच्छे-बुरे दोनों प्रभाव बढ़ाते हैं। पूरी कुंडली की समीक्षा के बाद ही धारण करें।"
                if hi else "Gemstones amplify a graha's effects, good and bad. Wear one only after a full-chart review by an expert."),
        "target": 1, "weekday": None,
    }
