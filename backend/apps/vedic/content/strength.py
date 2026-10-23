"""'What to do' guidance for Shadbala (grahas) and Bhava Bala (houses)."""
from .common import HINDI, SANSKRIT, WEEKDAY, PLANET_DAY, ordinal

# Six sources: key -> (en name, en gloss, hi name, hi gloss)
SOURCES = {
    "sthana": ("Sthan", "position", "स्थान", "स्थिति"),
    "dig": ("Dig", "direction", "दिक्", "दिशा"),
    "kala": ("Kaal", "time", "काल", "समय"),
    "chesta": ("Cheshta", "motion", "चेष्टा", "गति"),
    "naisargika": ("Naisargik", "natural", "नैसर्गिक", "स्वाभाविक"),
    "drik": ("Drik", "aspects", "दृक्", "दृष्टि"),
}

STATUS = {
    "en": {"good": "Strong", "neutral": "Adequate", "bad": "Needs support"},
    "hi": {"good": "बलवान", "neutral": "पर्याप्त", "bad": "सहायता चाहिए"},
}


def status_of_ratio(ratio: float) -> str:
    return "good" if ratio >= 1.10 else "neutral" if ratio >= 1.0 else "bad"


def status_of_house(rupas: float) -> str:
    return "good" if rupas >= 8 else "neutral" if rupas >= 7 else "bad"


# planet -> {strong: (en head, [(t, d)...]), weak: ..., hi_strong, hi_weak}
_ADVICE = {
    "Su": {
        "strong": ("Surya is comfortably strong — authority and visibility come easily.",
                   [("Take the visible role", "Present, lead, sign your name to things."),
                    ("Morning sunlight", "A few minutes facing sunrise keeps it steady.")]),
        "weak": ("Surya is below its minimum — confidence and recognition need tending.",
                 [("Keep promises small and kept", "Self-trust grows from finished commitments."),
                  ("Mantra · Sundays", "Om Suryaya Namah, 108× at sunrise."),
                  ("Give", "Wheat or jaggery on Sundays."),
                  ("Honour your father", "Time with elders and mentors strengthens Surya.")]),
        "hi_strong": ("सूर्य सहज रूप से बलवान है — अधिकार और पहचान आसानी से मिलती है।",
                      [("आगे बढ़कर भूमिका लें", "प्रस्तुत करें, नेतृत्व करें, ज़िम्मेदारी लें।"),
                       ("सुबह की धूप", "उगते सूर्य के सामने कुछ मिनट बिताएँ।")]),
        "hi_weak": ("सूर्य न्यूनतम से कम है — आत्मविश्वास और पहचान पर ध्यान दें।",
                    [("छोटे वादे, पूरे वादे", "पूरे किए संकल्पों से आत्मविश्वास बढ़ता है।"),
                     ("मंत्र · रविवार", "ॐ सूर्याय नमः, सूर्योदय पर 108 बार।"),
                     ("दान", "रविवार को गेहूँ या गुड़।"),
                     ("पिता का सम्मान", "बड़ों और मार्गदर्शकों के साथ समय बिताएँ।")]),
    },
    "Mo": {
        "strong": ("Chandra is strong — the mind is steady and people respond to your care.",
                   [("Nurture", "Check in on family; your care lands well now."),
                    ("Trust your instinct", "Gut feelings are reliable — note them down.")]),
        "weak": ("Chandra is below its minimum — mind, sleep and emotional steadiness need tending.",
                 [("Keep a rhythm", "Regular sleep and meal times steady a weak Moon more than anything."),
                  ("Mantra · Mondays", "Om Somaya Namah, 108× in the evening."),
                  ("Give", "Rice, milk or white cloth on Mondays."),
                  ("Water", "Time near water — a walk, a swim, a long bath.")]),
        "hi_strong": ("चंद्र बलवान है — मन स्थिर है और लोग आपकी देखभाल को सराहते हैं।",
                      [("पोषण करें", "परिवार का हाल पूछें; आपकी परवाह असर करती है।"),
                       ("अंतर्ज्ञान पर भरोसा", "मन की आवाज़ भरोसेमंद है — उसे लिख लें।")]),
        "hi_weak": ("चंद्र न्यूनतम से कम है — मन, नींद और भावनात्मक स्थिरता पर ध्यान दें।",
                    [("नियमित दिनचर्या", "सोने और खाने का नियमित समय कमज़ोर चंद्र को सबसे अधिक सँभालता है।"),
                     ("मंत्र · सोमवार", "ॐ सोमाय नमः, शाम को 108 बार।"),
                     ("दान", "सोमवार को चावल, दूध या सफ़ेद वस्त्र।"),
                     ("जल", "जल के पास समय बिताएँ — सैर, तैराकी या लंबा स्नान।")]),
    },
    "Ma": {
        "strong": ("Mangal is strong — courage and drive are on tap.",
                   [("Channel it physically", "Daily exercise turns surplus heat into stamina."),
                    ("Start hard things on Tuesdays", "Use the day for tasks that need nerve.")]),
        "weak": ("Mangal is below its minimum — energy and assertiveness need building.",
                 [("Move every day", "Short, regular exercise rebuilds Mangal's fire."),
                  ("Mantra · Tuesdays", "Om Am Angarakaya Namah, 108×."),
                  ("Give", "Red lentils (masoor) on Tuesdays."),
                  ("Hanuman Chalisa", "Recite on Tuesdays for courage.")]),
        "hi_strong": ("मंगल बलवान है — साहस और ऊर्जा भरपूर है।",
                      [("शारीरिक रूप से लगाएँ", "रोज़ का व्यायाम अतिरिक्त ऊर्जा को सहनशक्ति में बदलता है।"),
                       ("कठिन काम मंगलवार को", "हिम्मत वाले काम इस दिन शुरू करें।")]),
        "hi_weak": ("मंगल न्यूनतम से कम है — ऊर्जा और दृढ़ता बढ़ाने की ज़रूरत है।",
                    [("रोज़ हलचल", "छोटा, नियमित व्यायाम मंगल की अग्नि बढ़ाता है।"),
                     ("मंत्र · मंगलवार", "ॐ अं अंगारकाय नमः, 108 बार।"),
                     ("दान", "मंगलवार को मसूर दाल।"),
                     ("हनुमान चालीसा", "साहस के लिए मंगलवार को पाठ करें।")]),
    },
    "Me": {
        "strong": ("Budh is strong — thinking, speech and trade flow well.",
                   [("Write and negotiate", "Your words land precisely now."),
                    ("Learn something", "Short courses and reading pay off quickly.")]),
        "weak": ("Budh is short of its minimum — focus and communication need support.",
                 [("Decide in writing", "Lists and notes compensate for scattered focus."),
                  ("Mantra · Wednesdays", "Budh beej mantra, 108×."),
                  ("Give", "Green gram (moong) on Wednesdays."),
                  ("Gemstone, with care", "Emerald only after a full-chart review.")]),
        "hi_strong": ("बुध बलवान है — सोच, वाणी और व्यापार अच्छे चलते हैं।",
                      [("लिखें और बात करें", "आपके शब्द सटीक असर करते हैं।"),
                       ("कुछ नया सीखें", "छोटे कोर्स और पढ़ाई जल्दी फल देते हैं।")]),
        "hi_weak": ("बुध न्यूनतम से कम है — एकाग्रता और संवाद को सहारा चाहिए।",
                    [("लिखकर निर्णय लें", "सूचियाँ और नोट्स बिखरे ध्यान की भरपाई करते हैं।"),
                     ("मंत्र · बुधवार", "बुध बीज मंत्र, 108 बार।"),
                     ("दान", "बुधवार को हरी मूँग।"),
                     ("रत्न, सावधानी से", "पन्ना केवल पूरी कुंडली देखने के बाद।")]),
    },
    "Ju": {
        "strong": ("Guru is strong — wisdom and good counsel flow through you.",
                   [("Teach & mentor", "Sharing what you know multiplies Guru's grace."),
                    ("Thursdays", "Favour study, advice and long-range plans.")]),
        "weak": ("Guru is below its minimum — faith, guidance and growth need nourishing.",
                 [("Seek a mentor", "Ask for counsel before big decisions."),
                  ("Mantra · Thursdays", "Om Brihaspataye Namah, 108×."),
                  ("Give", "Turmeric, chana dal or yellow cloth on Thursdays."),
                  ("Honour teachers", "Respect for gurus strengthens Guru.")]),
        "hi_strong": ("गुरु बलवान है — ज्ञान और अच्छी सलाह आपसे बहती है।",
                      [("सिखाएँ और मार्गदर्शन करें", "ज्ञान बाँटने से गुरु की कृपा बढ़ती है।"),
                       ("गुरुवार", "अध्ययन, सलाह और लंबी योजनाओं के लिए अनुकूल।")]),
        "hi_weak": ("गुरु न्यूनतम से कम है — आस्था, मार्गदर्शन और विकास को पोषण चाहिए।",
                    [("मार्गदर्शक खोजें", "बड़े फ़ैसलों से पहले सलाह लें।"),
                     ("मंत्र · गुरुवार", "ॐ बृहस्पतये नमः, 108 बार।"),
                     ("दान", "गुरुवार को हल्दी, चना दाल या पीला वस्त्र।"),
                     ("गुरुजनों का सम्मान", "गुरुओं का आदर गुरु ग्रह को बल देता है।")]),
    },
    "Ve": {
        "strong": ("Shukra is above its minimum — relationships and beauty return well.",
                   [("Invest in partnership", "Time given to people and craft compounds now."),
                    ("Fridays", "Good for social, creative and comfort plans.")]),
        "weak": ("Shukra is below its minimum — relationships, comfort and joy need care.",
                 [("Make room for beauty", "Music, art or flowers at home lift Shukra."),
                  ("Mantra · Fridays", "Om Shukraya Namah, 108×."),
                  ("Give", "White sweets, rice or curd on Fridays."),
                  ("Gentle with partners", "Small kindnesses repair more than big gestures.")]),
        "hi_strong": ("शुक्र न्यूनतम से ऊपर है — संबंध और सौंदर्य अच्छा फल देते हैं।",
                      [("साझेदारी में निवेश", "लोगों और कला को दिया समय अभी बढ़ता है।"),
                       ("शुक्रवार", "सामाजिक, रचनात्मक और आराम की योजनाओं के लिए अच्छा।")]),
        "hi_weak": ("शुक्र न्यूनतम से कम है — संबंध, सुख और आनंद को देखभाल चाहिए।",
                    [("सौंदर्य को जगह दें", "घर में संगीत, कला या फूल शुक्र को बल देते हैं।"),
                     ("मंत्र · शुक्रवार", "ॐ शुक्राय नमः, 108 बार।"),
                     ("दान", "शुक्रवार को सफ़ेद मिठाई, चावल या दही।"),
                     ("साथी के साथ कोमलता", "छोटी दयालुताएँ बड़े दिखावों से अधिक सुधारती हैं।")]),
    },
    "Sa": {
        "strong": ("Shani is strong — discipline and patience bring lasting results.",
                   [("Build slowly", "Long projects and structures hold well now."),
                    ("Saturdays", "Good for planning, cleaning up and hard work.")]),
        "weak": ("Shani is below its minimum — patience, discipline and structure need support.",
                 [("Small, steady routines", "Consistency over intensity; finish what you start."),
                  ("Mantra · Saturdays", "Om Sham Shanaishcharaya Namah, 108×."),
                  ("Serve", "Help elders or workers; give black sesame or mustard oil."),
                  ("Avoid shortcuts", "No blue sapphire without an expert review.")]),
        "hi_strong": ("शनि बलवान है — अनुशासन और धैर्य स्थायी परिणाम देते हैं।",
                      [("धीरे-धीरे बनाएँ", "लंबी परियोजनाएँ और ढाँचे अभी टिकते हैं।"),
                       ("शनिवार", "योजना, सफ़ाई और मेहनत के लिए अच्छा।")]),
        "hi_weak": ("शनि न्यूनतम से कम है — धैर्य, अनुशासन और व्यवस्था को सहारा चाहिए।",
                    [("छोटी, नियमित दिनचर्या", "तीव्रता से अधिक निरंतरता; जो शुरू करें उसे पूरा करें।"),
                     ("मंत्र · शनिवार", "ॐ शं शनैश्चराय नमः, 108 बार।"),
                     ("सेवा", "बुज़ुर्गों या श्रमिकों की मदद करें; काले तिल या सरसों का तेल दान करें।"),
                     ("शॉर्टकट से बचें", "विशेषज्ञ की सलाह बिना नीलम न पहनें।")]),
    },
}


def planet_advice(code: str, kind: str, lang: str) -> dict:
    a = _ADVICE[code]
    key = ("hi_" if lang == "hi" else "") + ("weak" if kind == "bad" else "strong")
    head, items = a[key]
    return {"head": head, "items": [{"title": t, "detail": d} for t, d in items]}


def dasha_note(lord: str, kind: str, lang: str) -> str:
    if lang == "hi":
        return (f"आपकी महादशा का स्वामी {HINDI[lord]} न्यूनतम से कम है, इसलिए इसे सहारा देना पूरे अध्याय में लाभ देगा।"
                if kind == "bad" else f"आपकी महादशा का स्वामी {HINDI[lord]} पर्याप्त बलवान है — यह अध्याय अपने परिणाम दे सकता है।")
    return (f"{SANSKRIT[lord]} — your Mahadasha lord — is below its minimum, so supporting it pays off across this whole chapter."
            if kind == "bad" else f"{SANSKRIT[lord]} — your Mahadasha lord — is strong enough to deliver this chapter's results.")


# house -> (en strong, en weak, hi strong, hi weak); lists of advice lines
_HOUSE = {
    1: (["Your body and presence carry you — invest in health habits that compound.", "A good house to act from: start things in your own name."],
        ["Protect your energy — sleep, food and movement come first.", "Avoid over-committing; say no early."],
        ["आपका शरीर और व्यक्तित्व आपका साथ देते हैं — स्वास्थ्य की आदतों में निवेश करें।", "अपने नाम से काम शुरू करने के लिए अच्छा भाव।"],
        ["अपनी ऊर्जा बचाएँ — नींद, भोजन और व्यायाम पहले।", "ज़्यादा वादे न करें; जल्दी मना करना सीखें।"]),
    2: (["Savings and family ties grow steadily — keep feeding them.", "Your words persuade; use them for good."],
        ["Speak slowly on money and family matters.", "Keep a simple weekly savings ritual."],
        ["बचत और पारिवारिक संबंध स्थिर बढ़ते हैं — इन्हें पोषित करते रहें।", "आपके शब्द प्रभावी हैं; उनका सदुपयोग करें।"],
        ["धन और परिवार की बात धीरे करें।", "हर हफ़्ते बचत का एक सरल नियम रखें।"]),
    3: (["Effort pays off — short trips, writing and outreach are favoured."],
        ["Pick one effort and finish it before starting another.", "Stay in touch with siblings; small gestures matter."],
        ["प्रयास फल देते हैं — छोटी यात्राएँ, लेखन और संपर्क अनुकूल हैं।"],
        ["एक प्रयास चुनें और दूसरा शुरू करने से पहले उसे पूरा करें।", "भाई-बहनों से संपर्क रखें; छोटे प्रयास मायने रखते हैं।"]),
    4: (["Home is a source of strength — host, rest and root yourself there."],
        ["Make home a place of rest — clear one corner this week.", "Spend unhurried time with your mother or elders."],
        ["घर शक्ति का स्रोत है — वहाँ आतिथ्य करें, विश्राम करें, जड़ें मज़बूत करें।"],
        ["घर को विश्राम का स्थान बनाएँ — इस हफ़्ते एक कोना साफ़ करें।", "माँ या बड़ों के साथ इत्मीनान से समय बिताएँ।"]),
    5: (["Creative and learning projects flow — begin one.", "Good house for time with children and play."],
        ["Protect your focus; one creative project at a time.", "Avoid speculation until this house steadies."],
        ["रचनात्मक और सीखने की परियोजनाएँ सहज हैं — एक शुरू करें।", "बच्चों के साथ समय और खेल के लिए अच्छा भाव।"],
        ["ध्यान बचाएँ; एक समय में एक रचनात्मक काम।", "यह भाव स्थिर होने तक सट्टे से बचें।"]),
    6: (["You overcome obstacles well — tackle the hardest task first."],
        ["Guard health with fixed sleep and meal times.", "Settle small debts and disputes promptly."],
        ["आप बाधाओं को अच्छी तरह पार करते हैं — सबसे कठिन काम पहले करें।"],
        ["नियमित नींद और भोजन से स्वास्थ्य की रक्षा करें।", "छोटे ऋण और विवाद जल्दी सुलझाएँ।"]),
    7: (["Partnerships support you — collaborate and sign with confidence."],
        ["Read contracts twice; don't rush commitments.", "Listen before negotiating — partnerships need patience now."],
        ["साझेदारी आपका साथ देती है — सहयोग करें और भरोसे से अनुबंध करें।"],
        ["अनुबंध दो बार पढ़ें; प्रतिबद्धता में जल्दी न करें।", "मोलभाव से पहले सुनें — साझेदारी को अभी धैर्य चाहिए।"]),
    8: (["Resilience is high — research and deep work go well."],
        ["Keep a buffer for sudden expenses.", "Avoid speculation and high-risk ventures."],
        ["सहनशक्ति अधिक है — शोध और गहन काम अच्छे चलते हैं।"],
        ["अचानक खर्चों के लिए गुंजाइश रखें।", "सट्टा और जोखिम भरे उपक्रमों से बचें।"]),
    9: (["Fortune favours study, travel and seeking a mentor.", "Honour teachers and your father — it amplifies this house."],
        ["Return to a practice or teacher that steadies you.", "Plan long journeys carefully."],
        ["भाग्य अध्ययन, यात्रा और मार्गदर्शक की खोज का साथ देता है।", "गुरुओं और पिता का सम्मान करें — यह इस भाव को बल देता है।"],
        ["किसी ऐसे अभ्यास या गुरु की ओर लौटें जो आपको स्थिर करे।", "लंबी यात्राओं की योजना सावधानी से बनाएँ।"]),
    10: (["Career is a strong house — ask for the role, pitch the idea.", "Act during Abhijit Muhurat for professional starts."],
         ["Do the essentials well; visibility can wait.", "Avoid workplace conflicts this period."],
         ["करियर बलवान भाव है — भूमिका माँगें, विचार रखें।", "पेशेवर शुरुआत अभिजित मुहूर्त में करें।"],
         ["ज़रूरी काम अच्छे से करें; दिखावा इंतज़ार कर सकता है।", "इस अवधि में कार्यस्थल के विवादों से बचें।"]),
    11: (["Networks bring gains — reconnect with old contacts.", "Group efforts outperform solo ones now."],
         ["Give without keeping score; gains return slowly.", "Choose a few close allies over a wide circle."],
         ["संपर्क लाभ लाते हैं — पुराने परिचितों से फिर जुड़ें।", "अभी अकेले से अधिक समूह के प्रयास सफल होते हैं।"],
         ["बिना हिसाब रखे दें; लाभ धीरे लौटते हैं।", "बड़े दायरे से अधिक कुछ करीबी साथी चुनें।"]),
    12: (["Rest and retreat restore you deeply — protect quiet time."],
         ["Guard your sleep; screens off an hour before bed.", "Budget travel and giving so outflows feel chosen.",
          "A quiet practice — meditation or a short retreat — restores this house."],
         ["विश्राम और एकांत आपको गहराई से पुनर्जीवित करते हैं — शांत समय बचाएँ।"],
         ["नींद की रक्षा करें; सोने से एक घंटा पहले स्क्रीन बंद।", "यात्रा और दान का बजट बनाएँ ताकि खर्च सोच-समझकर हों।",
          "एक शांत अभ्यास — ध्यान या छोटा एकांतवास — इस भाव को फिर से भरता है।"]),
}


def house_advice(house: int, kind: str, lord: str, lang: str) -> list[str]:
    en_s, en_w, hi_s, hi_w = _HOUSE[house]
    weak = kind == "bad"
    lines = list((hi_w if weak else hi_s) if lang == "hi" else (en_w if weak else en_s))
    if weak:
        day = WEEKDAY[lang][PLANET_DAY[lord]]
        if lang == "hi":
            lines.append(f"{day}: {ordinal(house, 'hi')} भाव के स्वामी {HINDI[lord]} के मंत्र या दान से सहारा दें।")
        else:
            lines.append(f"{day}s: support the {ordinal(house, 'en')} lord ({SANSKRIT[lord]}) with its mantra or charity.")
    return lines


BHAVA_COMPONENTS = {
    "bhavadhipati": ("Bhavadhipati · lord", "भावाधिपति · स्वामी"),
    "dig": ("Dig · direction", "दिक् · दिशा"),
    "drishti": ("Drishti · aspects", "दृष्टि · दृष्टियाँ"),
    "other": ("Occupants & time", "स्थित ग्रह और समय"),
}
