"""Life goals a user can work towards, and which graha support each one."""

# key -> glyph, (label en, label hi), (blurb en, blurb hi), karaka graha, houses (bhava numbers)
_GOALS = {
    "marriage": ("❦", ("Getting married", "विवाह"),
                 ("Shukra and Guru, with your 7th house lord", "शुक्र, गुरु और सप्तम भाव के स्वामी"),
                 ("Ve", "Ju"), (7,)),
    "career": ("▲", ("Getting a job / career", "नौकरी / करियर"),
               ("Shani, Surya and Budh, with your 10th house lord", "शनि, सूर्य, बुध और दशम भाव के स्वामी"),
               ("Sa", "Su", "Me"), (10,)),
    "wealth": ("◎", ("Wealth & money", "धन-समृद्धि"),
               ("Guru and Shukra, with your 2nd and 11th house lords", "गुरु, शुक्र और द्वितीय व एकादश भाव के स्वामी"),
               ("Ju", "Ve"), (2, 11)),
    "health": ("✚", ("Health & vitality", "स्वास्थ्य"),
               ("Surya and Chandra, with your lagna lord", "सूर्य, चंद्र और लग्न के स्वामी"),
               ("Su", "Mo"), (1, 6)),
    "education": ("✎", ("Education & exams", "शिक्षा व परीक्षा"),
                  ("Budh and Guru, with your 5th house lord", "बुध, गुरु और पंचम भाव के स्वामी"),
                  ("Me", "Ju"), (5, 4)),
    "children": ("❀", ("Children", "संतान"),
                 ("Guru, with your 5th house lord", "गुरु और पंचम भाव के स्वामी"),
                 ("Ju",), (5,)),
    "peace": ("☾", ("Peace of mind", "मानसिक शांति"),
              ("Chandra and Ketu, with your 4th house lord", "चंद्र, केतु और चतुर्थ भाव के स्वामी"),
              ("Mo", "Ke"), (4,)),
    "property": ("⌂", ("Home & property", "घर व संपत्ति"),
                 ("Mangal and Shukra, with your 4th house lord", "मंगल, शुक्र और चतुर्थ भाव के स्वामी"),
                 ("Ma", "Ve"), (4,)),
    "foreign": ("✈", ("Going abroad", "विदेश यात्रा"),
                ("Rahu, with your 12th house lord", "राहु और द्वादश भाव के स्वामी"),
                ("Ra",), (12,)),
    "legal": ("⚖", ("Winning disputes", "विवाद / मुकदमे में जीत"),
              ("Shani and Mangal, with your 6th house lord", "शनि, मंगल और षष्ठ भाव के स्वामी"),
              ("Sa", "Ma"), (6,)),
}

GOAL_KEYS = tuple(_GOALS)
MAX_GOALS = 3   # with Pro
FREE_GOALS = 1  # on the free plan

# One-word names for badges (en, hi).
_SHORT = {
    "marriage": ("Marriage", "विवाह"), "career": ("Career", "करियर"), "wealth": ("Wealth", "धन"),
    "health": ("Health", "स्वास्थ्य"), "education": ("Education", "शिक्षा"), "children": ("Children", "संतान"),
    "peace": ("Peace", "शांति"), "property": ("Property", "संपत्ति"), "foreign": ("Abroad", "विदेश"),
    "legal": ("Disputes", "विवाद"),
}


def goal(key: str, lang: str) -> dict:
    glyph, label, blurb, karakas, houses = _GOALS[key]
    i = 1 if lang == "hi" else 0
    return {"key": key, "glyph": glyph, "label": label[i], "short": _SHORT[key][i], "blurb": blurb[i],
            "planets": list(karakas), "houses": list(houses)}


def short_label(key: str, lang: str) -> str:
    return _SHORT[key][1 if lang == "hi" else 0] if key in _SHORT else ""


def catalogue(lang: str) -> list[dict]:
    return [goal(k, lang) for k in GOAL_KEYS]


def label(key: str, lang: str) -> str:
    return _GOALS[key][1][1 if lang == "hi" else 0] if key in _GOALS else ""


def planets_for(key: str, house_lords: dict[int, str] | None, limit: int = 2) -> list[str]:
    """Graha to strengthen for a goal: the chart's lord of the goal's main house first (when known),
    then the natural karakas. `house_lords` maps bhava number -> lord code."""
    _, _, _, karakas, houses = _GOALS[key]
    out: list[str] = []
    if house_lords:
        lord = house_lords.get(houses[0])
        if lord:
            out.append(lord)
    for p in karakas:
        if p not in out:
            out.append(p)
    return out[:limit]
