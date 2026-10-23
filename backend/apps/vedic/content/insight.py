"""Templates for the daily insight (moon transit house + dasha lord condition)."""
from .common import HINDI, HOUSE_MEANING, SANSKRIT, ENGLISH, ordinal

# house (from lagna) -> (en supportive, en testing, hi supportive, hi testing)
HOUSE_THEME = {
    1: ("A day to show up as yourself — energy gathers around you.",
        "Your energy runs thinner today; protect it before you spend it.",
        "आज अपने स्वरूप में आगे आने का दिन है — ऊर्जा आपके साथ है।",
        "आज ऊर्जा कुछ कम है; खर्च करने से पहले उसे सँभालें।"),
    2: ("Words carry weight today — speak about money and family with care and they land well.",
        "Go slowly with money and words today; small slips cost more than usual.",
        "आज शब्दों में वज़न है — धन और परिवार की बात सोच-समझकर करें, असर अच्छा होगा।",
        "आज धन और वाणी में धीमे चलें; छोटी चूक भी भारी पड़ सकती है।"),
    3: ("Effort pays today — reach out, write, take the short trip.",
        "Effort feels uphill today; keep outreach small and specific.",
        "आज प्रयास फल देंगे — संपर्क करें, लिखें, छोटी यात्रा करें।",
        "आज प्रयास भारी लग सकते हैं; संपर्क छोटे और सटीक रखें।"),
    4: ("A steady day for home and inner ground.",
        "Home and heart ask for quiet today; don't force the outer world.",
        "घर और मन की स्थिरता का दिन है।",
        "आज घर और मन शांति चाहते हैं; बाहर की दुनिया पर ज़ोर न डालें।"),
    5: ("Creativity and play come easily — make something.",
        "The mind wanders today; choose one creative thread and stay with it.",
        "रचनात्मकता सहज है — कुछ नया बनाइए।",
        "आज मन भटक सकता है; एक ही रचनात्मक काम चुनें और उसी पर टिके रहें।"),
    6: ("A good day to clear the backlog — health, chores and small debts.",
        "Routine feels heavy today; care for the body first.",
        "लंबित कामों को निपटाने का अच्छा दिन — स्वास्थ्य, घर के काम और छोटे ऋण।",
        "आज दिनचर्या भारी लगेगी; पहले शरीर का ध्यान रखें।"),
    7: ("Partnerships open up — a good day to meet halfway.",
        "Others feel less predictable today; listen longer before you agree.",
        "साझेदारी के रास्ते खुलते हैं — आधे रास्ते मिलने का अच्छा दिन।",
        "आज दूसरों का व्यवहार अनिश्चित रहेगा; हाँ कहने से पहले ज़्यादा सुनें।"),
    8: ("A day for depth — research, reflect, look beneath the surface.",
        "Undercurrents run strong today; avoid risks and keep a buffer.",
        "गहराई का दिन — शोध करें, सोचें, सतह के नीचे देखें।",
        "आज भीतर की धाराएँ तेज़ हैं; जोखिम से बचें और गुंजाइश रखें।"),
    9: ("Fortune leans your way — study, seek counsel, plan the longer arc.",
        "Faith may waver today; return to a teacher or a text that steadies you.",
        "भाग्य साथ है — अध्ययन करें, सलाह लें, लंबी योजना बनाएँ।",
        "आज आस्था डगमगा सकती है; किसी गुरु या ग्रंथ की ओर लौटें।"),
    10: ("Work moves well today — ask for the role, pitch the idea.",
         "Work demands more than usual today; do the essential and let the rest wait.",
         "आज काम अच्छी गति से चलेगा — भूमिका माँगें, विचार रखें।",
         "आज काम ज़्यादा माँगेगा; ज़रूरी करें, बाकी इंतज़ार कर सकता है।"),
    11: ("Gains and goodwill flow — reconnect with your network.",
         "Expectations of others may not land today; give without keeping score.",
         "लाभ और सद्भाव बहते हैं — अपने संपर्कों से फिर जुड़ें।",
         "आज दूसरों से उम्मीदें पूरी न हों; बिना हिसाब रखे दें।"),
    12: ("A quiet day for rest, retreat and letting go.",
         "Energy drains easily today; guard your sleep and your spending.",
         "विश्राम, एकांत और छोड़ने का शांत दिन।",
         "आज ऊर्जा जल्दी घटेगी; नींद और खर्च दोनों सँभालें।"),
}

# dasha-lord transit condition -> (en clause, en reason, hi clause, hi reason)
LORD_STATE = {
    "retrograde": ("Finish before you start — return to something you left half-done.",
                   "sits retrograde, which favours revisiting and completing over launching anew.",
                   "शुरू करने से पहले पूरा करें — अधूरे छोड़े काम पर लौटें।",
                   "वक्री है, इसलिए नया शुरू करने से अधिक पुराने को पूरा करना अनुकूल है।"),
    "combust": ("Work quietly; results come before recognition.",
                "is close to the Sun, so quiet effort works better than visibility.",
                "चुपचाप काम करें; पहचान से पहले परिणाम आएँगे।",
                "सूर्य के निकट है, इसलिए दिखावे से अधिक शांत प्रयास काम आएगा।"),
    "favourable": ("Move ahead with what is already in motion.",
                   "transits a supportive house from your Moon, backing steady progress.",
                   "जो काम चल रहा है उसे आगे बढ़ाएँ।",
                   "आपके चंद्र से अनुकूल भाव में गोचर कर रहा है, जो स्थिर प्रगति का साथ देता है।"),
    "strained": ("Pace yourself — consistency beats intensity today.",
                 "is under strain in transit, so pace yourself rather than push.",
                 "अपनी गति संतुलित रखें — आज तीव्रता से अधिक निरंतरता काम आएगी।",
                 "गोचर में दबाव में है, इसलिए ज़ोर लगाने के बजाय गति संभालें।"),
}


def compose(moon_house: int, supportive: bool, lord: str, lord_state: str, lang: str) -> dict:
    theme = HOUSE_THEME[moon_house]
    state = LORD_STATE[lord_state]
    hi = lang == "hi"
    headline = theme[2 if supportive else 3] if hi else theme[0 if supportive else 1]
    text = f"{headline} {state[2] if hi else state[0]}"
    meaning = HOUSE_MEANING[lang][moon_house - 1]
    if hi:
        why = (f"आज चंद्रमा आपके {ordinal(moon_house, 'hi')} भाव ({meaning}) से गोचर कर रहा है — "
               f"जन्म चंद्र से यह {'सहायक' if supportive else 'परीक्षा भरी'} स्थिति है। "
               f"आपकी दशा का स्वामी {HINDI[lord]} {state[3]}")
        chips = [f"चंद्र · {moon_house} भाव",
                 f"{HINDI[lord]}{' ℞' if lord_state == 'retrograde' else ''} दशा"]
    else:
        why = (f"The Moon transits your {ordinal(moon_house, 'en')} house ({meaning}) today — "
               f"a {'supportive' if supportive else 'testing'} position from your birth Moon. "
               f"{ENGLISH[lord]} ({SANSKRIT[lord]}), your Dasha lord, {state[1]}")
        chips = [f"Chandra · {ordinal(moon_house, 'en')} house",
                 f"{SANSKRIT[lord]}{' ℞' if lord_state == 'retrograde' else ''} Dasha"]
    return {"text": text, "why": why, "chips": chips}


# Transit gloss: planet + house -> short phrase (shown under "Mars enters 10th").
_PLANET_DRIVE = {
    "Su": ("visibility", "प्रतिष्ठा"), "Mo": ("feelings", "भावनाएँ"), "Ma": ("drive", "ऊर्जा"),
    "Me": ("thinking", "सोच"), "Ju": ("growth", "विकास"), "Ve": ("pleasure", "आनंद"),
    "Sa": ("pressure", "दबाव"), "Ra": ("ambition", "महत्वाकांक्षा"), "Ke": ("detachment", "वैराग्य"),
}
_HOUSE_AREA = {
    "en": ["in yourself", "around money", "in your efforts", "at home", "in creative work", "in daily work",
           "in partnerships", "beneath the surface", "in beliefs & study", "at work", "in your network", "in rest & retreat"],
    "hi": ["अपने भीतर", "धन के मामलों में", "आपके प्रयासों में", "घर में", "रचनात्मक काम में", "रोज़ के काम में",
           "साझेदारी में", "भीतर ही भीतर", "आस्था और अध्ययन में", "कार्यक्षेत्र में", "आपके संपर्कों में", "विश्राम और एकांत में"],
}


def transit_title(planet: str, house: int, fresh: bool, lang: str) -> dict:
    drive_en, drive_hi = _PLANET_DRIVE[planet]
    area = _HOUSE_AREA[lang][house - 1]
    if lang == "hi":
        verb = "में प्रवेश" if fresh else "में"
        return {"title": f"{HINDI[planet]} {house} भाव {verb}", "gloss": f"{area} {drive_hi} पर ज़ोर"}
    verb = "enters" if fresh else "in"
    return {"title": f"{ENGLISH[planet]} {verb} {ordinal(house, 'en')}",
            "gloss": f"{drive_en.capitalize()} sharpens {area}"}
