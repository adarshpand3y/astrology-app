"""Remedy catalogue: mantra, fasting, charity and gemstone for each graha."""
from .common import HINDI, SANSKRIT, WEEKDAY, PLANET_DAY

KINDS = ("mantra", "fast", "charity", "gem")  # per graha; "seva", "puja" and "element" are chart-wide
KIND_GLYPH = {"mantra": "ॐ", "fast": "◐", "charity": "❋", "gem": "◆", "seva": "✿", "puja": "✺", "element": "◈"}
KIND_LABEL = {"en": {"mantra": "Mantra", "fast": "Fasting", "charity": "Charity", "gem": "Gemstone", "seva": "Seva",
                     "puja": "Puja", "element": "Tattva"},
              "hi": {"mantra": "मंत्र", "fast": "व्रत", "charity": "दान", "gem": "रत्न", "seva": "सेवा",
                     "puja": "पूजा", "element": "तत्व"}}
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


# Gau seva for grahas born in Gandmool nakshatras: no graha of its own, every day.
SEVA = {
    "en": {"title": "Gau seva · feed hara chara", "cadence": "about 15 min · daily",
           "how": "Spend about 15 minutes near a cow and feed it fresh hara chara (green fodder) with your own "
                  "hands. Gau seva calms the grahas that were in Gandmool nakshatras when you were born."},
    "hi": {"title": "गौ सेवा · हरा चारा खिलाएँ", "cadence": "लगभग 15 मिनट · रोज़",
           "how": "लगभग 15 मिनट गाय के पास बिताएँ और अपने हाथों से उसे ताज़ा हरा चारा खिलाएँ। गौ सेवा उन ग्रहों को "
                  "शांत करती है जो आपके जन्म के समय गंडमूल नक्षत्र में थे।"},
}


# Gandmool shanti puja for a Chandra born in a Gandmool nakshatra: done once, not daily.
SHANTI = {
    "en": {"title": "Gandmool shanti puja", "cadence": "once",
           "how": "A one-time puja, traditionally done on a day when Chandra returns to your birth nakshatra "
                  "(about every 27 days). A priest performs it at home or in a temple: Ganesh puja, Navagraha "
                  "shanti, the nakshatra lord's mantra and a havan. Mark it done once it is complete."},
    "hi": {"title": "गंडमूल शांति पूजा", "cadence": "एक बार",
           "how": "एक बार की पूजा, परंपरा से उस दिन जब चंद्र आपके जन्म नक्षत्र में लौटे (लगभग हर 27 दिन)। "
                  "पुरोहित इसे घर या मंदिर में कराते हैं: गणेश पूजा, नवग्रह शांति, नक्षत्र स्वामी का मंत्र और हवन। "
                  "पूरी होने पर इसे पूर्ण चिह्नित करें।"},
}

# The lagna's element (tattva, from SIGN_TATVA) -> a daily practice to connect with it.
ELEMENTS = ("Fire", "Earth", "Air", "Water")
ELEMENT_NAME = {"Fire": ("Agni (fire)", "अग्नि"), "Earth": ("Prithvi (earth)", "पृथ्वी"),
                "Air": ("Vayu (air)", "वायु"), "Water": ("Jal (water)", "जल")}
ELEMENT = {
    "Fire": {
        "en": {"title": "Agni tattva · Surya arghya", "cadence": "daily · at sunrise",
               "how": "Offer water to the rising Sun from a copper lota, then spend a few minutes facing its light. "
                      "At dusk, light a ghee deepak. Your lagna is a fire sign: tending a flame keeps your drive "
                      "warm without letting it burn out."},
        "hi": {"title": "अग्नि तत्व · सूर्य अर्घ्य", "cadence": "रोज़ · सूर्योदय पर",
               "how": "तांबे के लोटे से उगते सूर्य को जल अर्पित करें और कुछ मिनट उसके प्रकाश की ओर मुख करें। "
                      "संध्या को घी का दीपक जलाएँ। आपका लग्न अग्नि राशि है: दीपक की लौ आपके उत्साह को संतुलित रखती है।"},
    },
    "Earth": {
        "en": {"title": "Prithvi tattva · barefoot on the earth", "cadence": "about 15 min · daily",
               "how": "Walk barefoot on grass or soil for 10–15 minutes, and water or tend a plant (tulsi is "
                      "traditional). Your lagna is an earth sign: touching the ground keeps you steady and patient."},
        "hi": {"title": "पृथ्वी तत्व · नंगे पाँव धरती पर", "cadence": "लगभग 15 मिनट · रोज़",
               "how": "10–15 मिनट घास या मिट्टी पर नंगे पाँव चलें और किसी पौधे (परंपरा से तुलसी) को जल दें या "
                      "उसकी देखभाल करें। आपका लग्न पृथ्वी राशि है: धरती का स्पर्श आपको स्थिर और धैर्यवान रखता है।"},
    },
    "Air": {
        "en": {"title": "Vayu tattva · anulom-vilom", "cadence": "10 min · every morning",
               "how": "Practise anulom-vilom pranayama (alternate-nostril breathing) for 10 minutes in open air, "
                      "ideally at sunrise. Your lagna is an air sign: slow, even breath settles a busy mind."},
        "hi": {"title": "वायु तत्व · अनुलोम-विलोम", "cadence": "10 मिनट · हर सुबह",
               "how": "खुली हवा में, हो सके तो सूर्योदय पर, 10 मिनट अनुलोम-विलोम प्राणायाम करें। आपका लग्न वायु "
                      "राशि है: धीमी, सम श्वास चंचल मन को शांत करती है।"},
    },
    "Water": {
        "en": {"title": "Jal tattva · water to tulsi", "cadence": "daily · in the morning",
               "how": "Offer water to a tulsi or peepal in the morning, and drink water kept overnight in a "
                      "copper vessel. Your lagna is a water sign: these small rituals keep your feelings flowing "
                      "and clear."},
        "hi": {"title": "जल तत्व · तुलसी को जल", "cadence": "रोज़ · सुबह",
               "how": "सुबह तुलसी या पीपल को जल अर्पित करें और रात भर तांबे के पात्र में रखा जल पिएँ। आपका लग्न जल "
                      "राशि है: ये छोटे नियम भावनाओं को निर्मल और प्रवाहित रखते हैं।"},
    },
}
# No birth time, so no lagna: shown only until the next sync retires the remedy.
ELEMENT_UNKNOWN = {
    "en": {"title": "Lagna tattva", "cadence": "daily",
           "how": "Add your birth time to see the practice for your lagna's element."},
    "hi": {"title": "लग्न तत्व", "cadence": "रोज़", "how": "अपने लग्न के तत्व का अभ्यास देखने के लिए जन्म समय जोड़ें।"},
}


def element_name(element: str | None, lang: str) -> str:
    return ELEMENT_NAME[element][1 if lang == "hi" else 0] if element in ELEMENT_NAME else ""


def remedy(planet: str, kind: str, lang: str, element: str | None = None) -> dict:
    """Display data for one remedy (title, cadence, how & why...). `element` is the lagna's tattva,
    for the "element" kind."""
    hi = lang == "hi"
    lk = "hi" if hi else "en"
    if kind == "seva":
        return {**SEVA[lk], "text": "", "target": 1, "weekday": None}
    if kind == "puja":
        return {**SHANTI[lk], "text": "", "target": 1, "weekday": None, "once": True}
    if kind == "element":
        return {**(ELEMENT[element][lk] if element in ELEMENT else ELEMENT_UNKNOWN[lk]),
                "text": "", "target": 1, "weekday": None}
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


# Why a remedy is on the list regardless of goals: reason -> (badge en, badge hi, detail en, detail hi).
BASIS = {
    "lagna": ("Lagna", "लग्न", "For your lagna lord", "आपके लग्न स्वामी के लिए"),
    "moon": ("Chandra", "चंद्र", "For your Moon (Chandra)", "आपके चंद्रमा के लिए"),
    "mahadasha": ("Mahadasha", "महादशा", "For your Mahadasha lord", "आपकी महादशा के स्वामी के लिए"),
    "antardasha": ("Antardasha", "अंतर्दशा", "For your Antardasha lord", "आपकी अंतर्दशा के स्वामी के लिए"),
    "gandmool": ("Gandmool", "गंडमूल", "For your Moon, born in a Gandmool nakshatra",
                 "गंडमूल नक्षत्र में जन्मे आपके चंद्र के लिए"),
    "gandmool_birth": ("Gandmool", "गंडमूल", "For grahas born in Gandmool nakshatras: {planets}",
                       "जन्म के समय गंडमूल नक्षत्र में ग्रहों के लिए: {planets}"),
    "lagna_element": ("Lagna tattva", "लग्न तत्व", "For your lagna's element: {element}",
                      "आपके लग्न के तत्व के लिए: {element}"),
}


def basis_short(reasons: list[str], lang: str) -> str:
    """Badge for a chart remedy: the first reason, e.g. "Mahadasha"."""
    return BASIS[reasons[0]][1 if lang == "hi" else 0] if reasons and reasons[0] in BASIS else ""


def basis_label(reasons: list[str], lang: str, planets: list[str] = (), element: str | None = None) -> str:
    """All reasons, e.g. "For your Mahadasha lord · For your lagna lord". `planets` fills the grahas a
    "gandmool_birth" reason is for, `element` the tattva of a "lagna_element" one."""
    hi = lang == "hi"
    names = ", ".join((HINDI if hi else SANSKRIT)[p] for p in planets)
    return " · ".join(BASIS[r][3 if hi else 2].format(planets=names, element=element_name(element, lang))
                      for r in reasons if r in BASIS)
