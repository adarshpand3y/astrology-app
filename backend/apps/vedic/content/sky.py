"""What to do and what to avoid while a graha is retrograde, combust, exalted or debilitated.

Each entry: (en note, en do, en avoid, hi note, hi do, hi avoid). Notes may use {house} for the
house the graha is transiting, counted from the user's lagna (an ordinal: "10th" / "दसवें").
"""
from .common import ordinal

CONDITIONS = ("retrograde", "exalted", "debilitated", "combust")  # display order

# Condition badges: (en, hi).
LABEL = {
    "retrograde": ("(R) Retrograde", "(R) वक्री"),
    "combust": ("(C) Combust", "(C) अस्त"),
    "exalted": ("Exalted", "उच्च"),
    "debilitated": ("Debilitated", "नीच"),
}

_GUIDE = {
    "Su": {
        "exalted": (
            "Surya is exalted in Mesha: confidence, authority and vitality run high through your {house} house.",
            ["Take the lead on what matters", "Ask for recognition you've earned", "Offer water to the Sun at sunrise"],
            ["Arrogance or talking over others", "Clashing with seniors for the sake of it"],
            "सूर्य मेष में उच्च है: आपके {house} भाव में आत्मविश्वास, अधिकार और ऊर्जा प्रबल है।",
            ["ज़रूरी कामों में नेतृत्व करें", "अपने काम की पहचान माँगें", "सूर्योदय पर सूर्य को जल अर्पित करें"],
            ["अहंकार या दूसरों की बात काटना", "बेवजह बड़ों से टकराव"],
        ),
        "debilitated": (
            "Surya is weakest in Tula: self-belief dips and recognition comes slowly in your {house} house.",
            ["Steady routines and early mornings", "Respect your father and mentors", "Surya beej mantra on Sundays"],
            ["Ego battles with authority", "Seeking approval for every decision", "Big career moves made from doubt"],
            "सूर्य तुला में नीच है: आपके {house} भाव में आत्मविश्वास घटता है और पहचान धीरे मिलती है।",
            ["नियमित दिनचर्या और जल्दी उठना", "पिता और गुरुजनों का सम्मान करें", "रविवार को सूर्य बीज मंत्र"],
            ["अधिकारियों से अहं का टकराव", "हर निर्णय के लिए स्वीकृति खोजना", "संदेह में करियर के बड़े फ़ैसले"],
        ),
    },
    "Mo": {
        "exalted": (
            "Chandra is exalted in Vrishabha: the mind is calm and feelings are generous in your {house} house.",
            ["Nurture family and close friends", "Start habits you want to keep", "Rest well and eat simply"],
            ["Overindulging in comfort food or spending", "Taking calm for granted"],
            "चंद्र वृषभ में उच्च है: आपके {house} भाव में मन शांत और भावनाएँ उदार हैं।",
            ["परिवार और मित्रों का ध्यान रखें", "अच्छी आदतें शुरू करें", "भरपूर आराम और सादा भोजन"],
            ["आराम के भोजन या खर्च में अति", "शांति को हल्के में लेना"],
        ),
        "debilitated": (
            "Chandra is weakest in Vrischika: moods run deep and swing fast through your {house} house.",
            ["Journal or talk feelings through", "Milk or white things in charity on Mondays", "Early nights"],
            ["Big emotional decisions", "Brooding over old hurts", "Reacting to every message at once"],
            "चंद्र वृश्चिक में नीच है: आपके {house} भाव में मन गहरा और जल्दी बदलने वाला रहता है।",
            ["भावनाएँ लिखें या किसी से बात करें", "सोमवार को दूध या सफ़ेद वस्तु का दान", "जल्दी सोएँ"],
            ["भावनाओं में बड़े निर्णय", "पुरानी बातों पर कुढ़ना", "हर संदेश का तुरंत जवाब देना"],
        ),
        "combust": (
            "Near the new Moon, Chandra is hidden by the Sun: energy and moods run low.",
            ["Rest and keep the day simple", "Finish rather than start", "Quiet prayer or meditation"],
            ["Important decisions and new starts", "Late nights and overwork"],
            "अमावस्या के पास चंद्र सूर्य से ढका रहता है: ऊर्जा और मन कमज़ोर रहते हैं।",
            ["आराम करें, दिन सरल रखें", "नया शुरू करने के बजाय पुराना पूरा करें", "शांत प्रार्थना या ध्यान"],
            ["महत्वपूर्ण निर्णय और नई शुरुआत", "देर रात तक जागना और अधिक काम"],
        ),
    },
    "Ma": {
        "retrograde": (
            "Mangal moves backward through your {house} house: drive turns inward and old frustrations resurface.",
            ["Finish what's pending", "Revisit fitness or home repairs", "Channel anger into exercise"],
            ["Picking fights or ultimatums", "Elective surgery if it can wait", "Starting risky physical ventures"],
            "मंगल आपके {house} भाव में वक्री है: उत्साह भीतर मुड़ता है और पुरानी झुंझलाहट लौटती है।",
            ["अधूरे काम पूरे करें", "व्यायाम या घर की मरम्मत दोबारा देखें", "क्रोध को व्यायाम में लगाएँ"],
            ["झगड़े या अल्टीमेटम", "टल सके तो ऐच्छिक सर्जरी", "जोखिम भरे शारीरिक काम शुरू करना"],
        ),
        "exalted": (
            "Mangal is exalted in Makara: courage and disciplined energy are strong in your {house} house.",
            ["Tackle hard tasks head-on", "Start a fitness goal", "Push through stalled projects"],
            ["Bulldozing people", "Taking reckless risks because you feel unstoppable"],
            "मंगल मकर में उच्च है: आपके {house} भाव में साहस और अनुशासित ऊर्जा प्रबल है।",
            ["कठिन कामों का सीधा सामना करें", "फ़िटनेस का लक्ष्य शुरू करें", "रुके हुए काम आगे बढ़ाएँ"],
            ["दूसरों को दबाना", "जोश में लापरवाह जोखिम"],
        ),
        "debilitated": (
            "Mangal is weakest in Karka: drive can turn into irritability or sudden flare-ups in your {house} house.",
            ["Steady exercise to burn off heat", "Hanuman Chalisa on Tuesdays", "Cool down before replying"],
            ["Confrontations and ultimatums", "Rash driving or risky sport", "Elective surgery if it can wait"],
            "मंगल कर्क में नीच है: आपके {house} भाव में उत्साह चिड़चिड़ाहट या अचानक ग़ुस्से में बदल सकता है।",
            ["गर्मी निकालने के लिए नियमित व्यायाम", "मंगलवार को हनुमान चालीसा", "जवाब देने से पहले शांत हों"],
            ["टकराव और अल्टीमेटम", "तेज़ गाड़ी या जोखिम भरे खेल", "टल सके तो ऐच्छिक सर्जरी"],
        ),
        "combust": (
            "Close to the Sun, Mangal's energy runs low and tempers run short.",
            ["Pace yourself; rest between efforts", "Let others take the lead for now"],
            ["Confrontations", "Risky physical work or heavy lifting"],
            "सूर्य के पास मंगल की ऊर्जा कम और ग़ुस्सा जल्दी रहता है।",
            ["धीरे चलें, बीच-बीच में आराम करें", "अभी दूसरों को आगे रहने दें"],
            ["टकराव", "जोखिम भरा शारीरिक काम या भारी वज़न उठाना"],
        ),
    },
    "Me": {
        "retrograde": (
            "Budh moves backward through your {house} house: thinking turns inward and details slip.",
            ["Revisit drafts and unfinished work", "Reconnect with old contacts", "Back up files; re-read fine print"],
            ["Signing new contracts", "Buying phones or electronics", "Launching campaigns or big announcements"],
            "बुध आपके {house} भाव में वक्री है: सोच भीतर मुड़ती है और बारीकियाँ छूटती हैं।",
            ["पुराने मसौदे और अधूरे काम दोबारा देखें", "पुराने संपर्कों से जुड़ें", "फ़ाइलों का बैकअप लें, शर्तें दोबारा पढ़ें"],
            ["नए अनुबंध पर हस्ताक्षर", "फ़ोन या इलेक्ट्रॉनिक्स खरीदना", "अभियान या बड़ी घोषणाएँ"],
        ),
        "exalted": (
            "Budh is exalted in Kanya: analysis, writing and trade are sharp in your {house} house.",
            ["Write, plan and negotiate", "Study or learn a skill", "Sort out accounts and paperwork"],
            ["Overthinking every small choice", "Nitpicking people close to you"],
            "बुध कन्या में उच्च है: आपके {house} भाव में विश्लेषण, लेखन और व्यापार तीक्ष्ण हैं।",
            ["लिखें, योजना बनाएँ, बातचीत करें", "पढ़ाई या नया कौशल सीखें", "हिसाब और काग़ज़ात ठीक करें"],
            ["हर छोटी बात पर ज़रूरत से ज़्यादा सोचना", "अपनों में कमियाँ निकालना"],
        ),
        "debilitated": (
            "Budh is weakest in Meena: words blur and decisions go by feel in your {house} house.",
            ["Double-check numbers and messages", "Ask someone to review key documents", "Green gram in charity on Wednesdays"],
            ["Signing in a hurry", "Gossip and loose talk", "Trusting verbal promises"],
            "बुध मीन में नीच है: आपके {house} भाव में शब्द धुंधले और निर्णय भावना से होते हैं।",
            ["आँकड़े और संदेश दोबारा जाँचें", "ज़रूरी काग़ज़ किसी से दिखवाएँ", "बुधवार को हरी मूँग का दान"],
            ["जल्दबाज़ी में हस्ताक्षर", "गपशप और बेमतलब बातें", "मौखिक वादों पर भरोसा"],
        ),
        "combust": (
            "Close to the Sun, Budh's voice is drowned out by ego and haste.",
            ["Write it down before you say it", "Let others speak first in meetings"],
            ["Arguing to win", "Hasty emails, interviews or public statements"],
            "सूर्य के पास बुध की आवाज़ अहं और जल्दबाज़ी में दब जाती है।",
            ["बोलने से पहले लिख लें", "बैठकों में पहले दूसरों को बोलने दें"],
            ["जीतने के लिए बहस", "जल्दबाज़ी में ईमेल, साक्षात्कार या सार्वजनिक बयान"],
        ),
    },
    "Ju": {
        "retrograde": (
            "Guru moves backward through your {house} house: growth turns inward; time to review beliefs and plans.",
            ["Revisit studies or a past teacher", "Review investments and long-range plans", "Give to learning on Thursdays"],
            ["Big new investments", "Starting a new course or ceremony", "Taking advice without checking it"],
            "गुरु आपके {house} भाव में वक्री है: विकास भीतर की ओर मुड़ता है; विश्वास और योजनाओं की समीक्षा का समय।",
            ["पुरानी पढ़ाई या गुरु से फिर जुड़ें", "निवेश और लंबी योजनाओं की समीक्षा", "गुरुवार को शिक्षा के लिए दान"],
            ["बड़े नए निवेश", "नई पढ़ाई या अनुष्ठान शुरू करना", "बिना जाँचे सलाह मानना"],
        ),
        "exalted": (
            "Guru is exalted in Karka: wisdom, teachers and grace are unusually generous in your {house} house.",
            ["Seek counsel or a mentor", "Begin study or a long-range plan", "Give to learning on Thursdays"],
            ["Over-promising: exaltation tempts excess", "Preaching instead of listening"],
            "गुरु कर्क में उच्च है: आपके {house} भाव में ज्ञान, गुरु और कृपा असाधारण रूप से उदार हैं।",
            ["सलाहकार या गुरु से मार्गदर्शन लें", "पढ़ाई या लंबी योजना शुरू करें", "गुरुवार को शिक्षा के लिए दान"],
            ["ज़रूरत से ज़्यादा वादे: उच्च ग्रह अति की ओर ले जाता है", "सुनने के बजाय उपदेश देना"],
        ),
        "debilitated": (
            "Guru is weakest in Makara: faith wavers and good advice is harder to find in your {house} house.",
            ["Stick to proven, practical plans", "Turmeric or chana dal in charity on Thursdays", "Honour teachers and elders"],
            ["Blind faith in schemes or gurus", "Lending money casually", "Cutting ethical corners"],
            "गुरु मकर में नीच है: आपके {house} भाव में आस्था डगमगाती है और अच्छी सलाह कम मिलती है।",
            ["आज़माई हुई, व्यावहारिक योजनाओं पर टिकें", "गुरुवार को हल्दी या चना दाल का दान", "गुरुजनों और बड़ों का सम्मान"],
            ["योजनाओं या गुरुओं पर अंधविश्वास", "आसानी से पैसा उधार देना", "नैतिकता से समझौता"],
        ),
        "combust": (
            "Close to the Sun, Guru's blessings work quietly rather than visibly (Guru asta).",
            ["Keep new plans private until secure", "Honour elders and teachers"],
            ["Weddings, griha pravesh or major auspicious starts until it clears", "Big financial bets on \"sure things\""],
            "सूर्य के पास गुरु की कृपा दिखती नहीं, चुपचाप काम करती है (गुरु अस्त)।",
            ["नई योजनाएँ पक्की होने तक गोपनीय रखें", "बड़ों और गुरुजनों का सम्मान"],
            ["अस्त रहने तक विवाह, गृह प्रवेश या बड़े शुभ कार्य", "\"पक्की\" चीज़ों पर बड़े आर्थिक दाँव"],
        ),
    },
    "Ve": {
        "retrograde": (
            "Shukra moves backward through your {house} house: old loves, values and tastes come up for review.",
            ["Mend or reconnect with relationships", "Restore or repair beautiful things", "Review spending and what you value"],
            ["Starting a new relationship or wedding", "Luxury purchases", "Cosmetic procedures or drastic makeovers"],
            "शुक्र आपके {house} भाव में वक्री है: पुराने रिश्ते, मूल्य और रुचियाँ फिर सामने आते हैं।",
            ["रिश्तों को सँवारें या फिर जुड़ें", "सुंदर चीज़ों की मरम्मत करें", "खर्च और अपनी प्राथमिकताओं की समीक्षा"],
            ["नया रिश्ता या विवाह शुरू करना", "विलासिता की खरीद", "सौंदर्य प्रक्रियाएँ या बड़ा बदलाव"],
        ),
        "exalted": (
            "Shukra is exalted in Meena: love, art and comfort flow easily in your {house} house.",
            ["Spend time with your partner", "Create, decorate or enjoy music", "Express gratitude generously"],
            ["Overspending on pleasure", "Idealising someone beyond reality"],
            "शुक्र मीन में उच्च है: आपके {house} भाव में प्रेम, कला और सुख सहज बहते हैं।",
            ["साथी के साथ समय बिताएँ", "रचना, सजावट या संगीत का आनंद", "खुलकर आभार व्यक्त करें"],
            ["सुख पर ज़रूरत से ज़्यादा खर्च", "किसी को हक़ीक़त से ज़्यादा आदर्श मानना"],
        ),
        "debilitated": (
            "Shukra is weakest in Kanya: affection gets critical and comforts feel thin in your {house} house.",
            ["Small, practical kindnesses", "White sweets or curd in charity on Fridays", "Keep spending modest"],
            ["Criticising your partner", "Rushing into a relationship", "Expensive purchases to fill a gap"],
            "शुक्र कन्या में नीच है: आपके {house} भाव में स्नेह आलोचनात्मक और सुख फीका लगता है।",
            ["छोटे, व्यावहारिक स्नेह के काम", "शुक्रवार को सफ़ेद मिठाई या दही का दान", "खर्च सीमित रखें"],
            ["साथी की आलोचना", "जल्दबाज़ी में रिश्ता", "कमी भरने के लिए महँगी खरीद"],
        ),
        "combust": (
            "Close to the Sun, Shukra's grace is hidden (Shukra asta): not a time for auspicious unions.",
            ["Strengthen existing bonds quietly", "Keep celebrations simple"],
            ["Weddings and engagements until it clears", "Luxury purchases and jewellery"],
            "सूर्य के पास शुक्र की कृपा छिपी रहती है (शुक्र अस्त): शुभ संबंधों का समय नहीं।",
            ["मौजूदा रिश्तों को चुपचाप मज़बूत करें", "उत्सव सादे रखें"],
            ["अस्त रहने तक विवाह और सगाई", "विलासिता और गहनों की खरीद"],
        ),
    },
    "Sa": {
        "retrograde": (
            "Shani moves backward through your {house} house: old duties, debts and delays come back to be settled.",
            ["Settle old debts and obligations", "Finish long-pending work", "Serve the elderly or labourers on Saturdays"],
            ["New long-term commitments", "Property deals", "Cutting corners on responsibilities"],
            "शनि आपके {house} भाव में वक्री है: पुराने दायित्व, कर्ज़ और देरी निपटाने के लिए लौटते हैं।",
            ["पुराने कर्ज़ और दायित्व निपटाएँ", "लंबे समय से अटके काम पूरे करें", "शनिवार को बुज़ुर्गों या श्रमिकों की सेवा"],
            ["नई दीर्घकालिक प्रतिबद्धताएँ", "संपत्ति के सौदे", "ज़िम्मेदारियों से बचना"],
        ),
        "exalted": (
            "Shani is exalted in Tula: patience, fairness and steady effort pay off in your {house} house.",
            ["Commit to long-term goals", "Build systems and routines", "Act fairly in disputes"],
            ["Being harsh or rigid with others", "Overworking without rest"],
            "शनि तुला में उच्च है: आपके {house} भाव में धैर्य, न्याय और निरंतर प्रयास फल देते हैं।",
            ["लंबे लक्ष्यों के लिए प्रतिबद्ध हों", "व्यवस्था और दिनचर्या बनाएँ", "विवादों में न्याय से चलें"],
            ["दूसरों के साथ कठोर या ज़िद्दी होना", "बिना आराम के अधिक काम"],
        ),
        "debilitated": (
            "Shani is weakest in Mesha: impatience meets delay in your {house} house.",
            ["Slow down and do things properly", "Black sesame or mustard oil in charity on Saturdays", "Keep promises small and keep them"],
            ["Shortcuts and quick fixes", "Quitting a job in frustration", "Disrespecting elders or workers"],
            "शनि मेष में नीच है: आपके {house} भाव में अधीरता और देरी आमने-सामने हैं।",
            ["धीमे चलें, काम ठीक से करें", "शनिवार को काले तिल या सरसों के तेल का दान", "छोटे वादे करें और निभाएँ"],
            ["शॉर्टकट और जल्दबाज़ी के उपाय", "झुंझलाहट में नौकरी छोड़ना", "बड़ों या श्रमिकों का अनादर"],
        ),
        "combust": (
            "Close to the Sun, Shani's results are delayed and authority weighs heavily.",
            ["Be patient with delays", "Keep a low profile at work"],
            ["Starting a new job or long-term commitment", "Clashing with bosses or officials"],
            "सूर्य के पास शनि के फल देर से मिलते हैं और अधिकार का दबाव बढ़ता है।",
            ["देरी में धैर्य रखें", "काम पर सादगी से रहें"],
            ["नई नौकरी या दीर्घकालिक प्रतिबद्धता शुरू करना", "बॉस या अधिकारियों से टकराव"],
        ),
    },
    "Ra": {
        "retrograde": (
            "Rahu always moves backward: this is its natural motion, not a warning. It stirs ambition in your {house} house.",
            ["Explore networks, tech and new ideas", "Use the urge for change constructively"],
            ["Shortcuts and get-rich-quick offers", "Obsessing over one outcome"],
            "राहु सदा वक्री चलता है: यह उसकी स्वाभाविक गति है, चेतावनी नहीं। यह आपके {house} भाव में महत्वाकांक्षा जगाता है।",
            ["नेटवर्क, तकनीक और नए विचार खोजें", "बदलाव की इच्छा को सही दिशा दें"],
            ["शॉर्टकट और जल्दी अमीर बनने के प्रस्ताव", "एक ही परिणाम पर जुनून"],
        ),
        "exalted": (
            "Rahu is strong in Vrishabha: ambition finds practical, material outlets in your {house} house.",
            ["Pursue bold but grounded goals", "Learn new technology or markets"],
            ["Greed and over-accumulation", "Deals that look too good to be true"],
            "राहु वृषभ में बली है: आपके {house} भाव में महत्वाकांक्षा को व्यावहारिक रास्ते मिलते हैं।",
            ["साहसी पर ठोस लक्ष्य", "नई तकनीक या बाज़ार सीखें"],
            ["लालच और अति संग्रह", "हद से ज़्यादा अच्छे लगने वाले सौदे"],
        ),
        "debilitated": (
            "Rahu is weak in Vrischika: confusion, suspicion and hidden fears can grow in your {house} house.",
            ["Get facts before acting", "Durga or Rahu mantra on Saturdays", "Keep finances transparent"],
            ["Secret dealings", "Intoxicants and risky thrills", "Acting on rumours"],
            "राहु वृश्चिक में दुर्बल है: आपके {house} भाव में भ्रम, संदेह और छिपे डर बढ़ सकते हैं।",
            ["कदम उठाने से पहले तथ्य जानें", "शनिवार को दुर्गा या राहु मंत्र", "पैसों का हिसाब पारदर्शी रखें"],
            ["गुप्त सौदे", "नशा और जोखिम भरे रोमांच", "अफ़वाहों पर काम करना"],
        ),
    },
    "Ke": {
        "retrograde": (
            "Ketu always moves backward: its natural, inward-turning motion through your {house} house.",
            ["Meditation and quiet practice", "Let go of what has run its course"],
            ["Forcing clarity on vague matters", "Isolating from people who support you"],
            "केतु सदा वक्री चलता है: आपके {house} भाव में यह उसकी स्वाभाविक, भीतर की ओर गति है।",
            ["ध्यान और शांत साधना", "जो पूरा हो चुका उसे छोड़ दें"],
            ["अस्पष्ट बातों पर ज़बरदस्ती स्पष्टता", "सहारा देने वालों से दूरी बनाना"],
        ),
        "exalted": (
            "Ketu is strong in Vrischika: intuition and spiritual depth sharpen in your {house} house.",
            ["Research, healing or spiritual study", "Trust your quiet instincts"],
            ["Cutting people off abruptly", "Neglecting practical duties"],
            "केतु वृश्चिक में बली है: आपके {house} भाव में अंतर्ज्ञान और आध्यात्मिक गहराई बढ़ती है।",
            ["शोध, उपचार या आध्यात्मिक अध्ययन", "अपने शांत अंतर्ज्ञान पर भरोसा करें"],
            ["अचानक लोगों से नाता तोड़ना", "व्यावहारिक कर्तव्यों की उपेक्षा"],
        ),
        "debilitated": (
            "Ketu is weak in Vrishabha: restlessness and a sense of loss can creep into your {house} house.",
            ["Simple routines and grounding walks", "Ganesh puja or Ketu mantra on Tuesdays"],
            ["Sudden renunciations or big exits", "Ignoring small health signals"],
            "केतु वृषभ में दुर्बल है: आपके {house} भाव में बेचैनी और खोने का भाव आ सकता है।",
            ["सरल दिनचर्या और ज़मीन से जुड़ी सैर", "मंगलवार को गणेश पूजा या केतु मंत्र"],
            ["अचानक त्याग या बड़े निकास", "स्वास्थ्य के छोटे संकेतों की अनदेखी"],
        ),
    },
}


def guide(planet: str, condition: str, house: int, lang: str) -> dict | None:
    """{label, note, do, avoid} for a graha in a condition, or None if there's no guidance."""
    entry = _GUIDE.get(planet, {}).get(condition)
    if entry is None:
        return None
    o = 3 if lang == "hi" else 0
    note, do, avoid = entry[o], entry[o + 1], entry[o + 2]
    return {"label": LABEL[condition][1 if lang == "hi" else 0], "note": note.format(house=ordinal(house, lang)),
            "do": list(do), "avoid": list(avoid)}
