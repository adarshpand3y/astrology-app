"""Static Vedic astrology reference data (Parashara / BPHS conventions)."""

SU, MO, MA, ME, JU, VE, SA, RA, KE = "Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa", "Ra", "Ke"

PLANETS = [SU, MO, MA, ME, JU, VE, SA, RA, KE]
SEVEN_PLANETS = [SU, MO, MA, ME, JU, VE, SA]

PLANET_NAMES = {
    SU: "Sun", MO: "Moon", MA: "Mars", ME: "Mercury", JU: "Jupiter",
    VE: "Venus", SA: "Saturn", RA: "Rahu", KE: "Ketu",
}

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGNS_SANSKRIT = [
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
]
SIGN_LORDS = [MA, VE, ME, MO, SU, ME, VE, MA, JU, SA, SA, JU]

# sign index -> element
SIGN_TATVA = ["Fire", "Earth", "Air", "Water"] * 3

# Exaltation sign index and exact degree in that sign.
EXALTATION = {SU: (0, 10), MO: (1, 3), MA: (9, 28), ME: (5, 15), JU: (3, 5), VE: (11, 27), SA: (6, 20),
              RA: (1, 20), KE: (7, 20)}
DEBILITATION = {p: ((s + 6) % 12, d) for p, (s, d) in EXALTATION.items()}

# Moolatrikona: (sign index, from degree, to degree)
MOOLATRIKONA = {SU: (4, 0, 20), MO: (1, 3, 30), MA: (0, 0, 12), ME: (5, 15, 20), JU: (8, 0, 10),
                VE: (6, 0, 15), SA: (10, 0, 20), RA: (2, 0, 30), KE: (8, 0, 30)}

OWN_SIGNS = {SU: [4], MO: [3], MA: [0, 7], ME: [2, 5], JU: [8, 11], VE: [1, 6], SA: [9, 10],
             RA: [10], KE: [7]}

# Naisargika (natural) relationships: planet -> (friends, neutrals, enemies)
NATURAL_RELATIONS = {
    SU: ({MO, MA, JU}, {ME}, {VE, SA}),
    MO: ({SU, ME}, {MA, JU, VE, SA}, set()),
    MA: ({SU, MO, JU}, {VE, SA}, {ME}),
    ME: ({SU, VE}, {MA, JU, SA}, {MO}),
    JU: ({SU, MO, MA}, {SA}, {ME, VE}),
    VE: ({ME, SA}, {MA, JU}, {SU, MO}),
    SA: ({ME, VE}, {JU}, {SU, MO, MA}),
    RA: ({ME, VE, SA}, {JU}, {SU, MO, MA}),
    KE: ({ME, VE, SA}, {JU}, {SU, MO, MA}),
}

NAKSHATRA_SPAN = 360.0 / 27.0
PADA_SPAN = NAKSHATRA_SPAN / 4.0

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_DEITIES = [
    "Ashwini Kumaras", "Yama", "Agni", "Brahma", "Soma", "Rudra", "Aditi", "Brihaspati",
    "Sarpas", "Pitrs", "Bhaga", "Aryaman", "Savitr", "Tvashtr", "Vayu", "Indra-Agni",
    "Mitra", "Indra", "Nirriti", "Apas", "Vishvadevas", "Vishnu", "Vasus", "Varuna",
    "Aja Ekapada", "Ahir Budhnya", "Pushan",
]

# Vimshottari order and years (also the nakshatra lord sequence starting at Ashwini).
VIMSHOTTARI_ORDER = [KE, VE, SU, MO, MA, RA, JU, SA, ME]
VIMSHOTTARI_YEARS = {KE: 7, VE: 20, SU: 6, MO: 10, MA: 7, RA: 18, JU: 16, SA: 19, ME: 17}
VIMSHOTTARI_TOTAL = 120

NAKSHATRA_LORDS = [VIMSHOTTARI_ORDER[i % 9] for i in range(27)]
# Gandmool: the six nakshatras where a water sign ends and a fire sign begins (0-based): Ashwini,
# Ashlesha, Magha, Jyeshtha, Mula, Revati. Ketu rules three of them, Budh the other three.
GANDMOOL_NAKSHATRAS = frozenset({0, 8, 9, 17, 18, 26})

_D, _M, _R = "Deva", "Manushya", "Rakshasa"
NAKSHATRA_GANA = [
    _D, _M, _R, _M, _D, _M, _D, _D, _R, _R, _M, _M, _D, _R,
    _D, _R, _D, _R, _R, _M, _M, _D, _R, _R, _M, _M, _D,
]

NAKSHATRA_YONI = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat",
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", "Dog",
    "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant",
]

_NADI_CYCLE = ["Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi"]
NAKSHATRA_NADI = [_NADI_CYCLE[i % 6] for i in range(27)]

# Name syllables (akshar) for each of the 108 padas.
NAKSHATRA_AKSHAR = [
    ["Chu", "Che", "Cho", "La"], ["Li", "Lu", "Le", "Lo"], ["A", "I", "U", "E"],
    ["O", "Va", "Vi", "Vu"], ["Ve", "Vo", "Ka", "Ki"], ["Ku", "Gha", "Ng", "Chha"],
    ["Ke", "Ko", "Ha", "Hi"], ["Hu", "He", "Ho", "Da"], ["Di", "Du", "De", "Do"],
    ["Ma", "Mi", "Mu", "Me"], ["Mo", "Ta", "Ti", "Tu"], ["Te", "To", "Pa", "Pi"],
    ["Pu", "Sha", "Na", "Tha"], ["Pe", "Po", "Ra", "Ri"], ["Ru", "Re", "Ro", "Ta"],
    ["Ti", "Tu", "Te", "To"], ["Na", "Ni", "Nu", "Ne"], ["No", "Ya", "Yi", "Yu"],
    ["Ye", "Yo", "Bha", "Bhi"], ["Bhu", "Dha", "Pha", "Dha"], ["Bhe", "Bho", "Ja", "Ji"],
    ["Khi", "Khu", "Khe", "Kho"], ["Ga", "Gi", "Gu", "Ge"], ["Go", "Sa", "Si", "Su"],
    ["Se", "So", "Da", "Di"], ["Du", "Tha", "Jha", "Na"], ["De", "Do", "Cha", "Chi"],
]

# Varna by Moon sign.
SIGN_VARNA = ["Kshatriya", "Vaishya", "Shudra", "Brahmin"] * 3

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
    "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti",
]

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
WEEKDAYS_SANSKRIT = ["Ravivara", "Somavara", "Mangalavara", "Budhavara", "Guruvara",
                     "Shukravara", "Shanivara"]
WEEKDAY_LORDS = [SU, MO, MA, ME, JU, VE, SA]

# Chaldean order used for hora lords.
HORA_SEQUENCE = [SA, JU, MA, SU, VE, ME, MO]

LUNAR_MONTHS = [
    "Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
    "Ashwin", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna",
]

RITUS = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]

# BPHS combustion orbs (degrees from the Sun); second value applies when retrograde.
COMBUSTION_ORBS = {MO: (12, 12), MA: (17, 17), ME: (14, 12), JU: (11, 11), VE: (10, 8), SA: (15, 15)}

BENEFICS_NATURAL = {JU, VE, ME}  # Moon depends on paksha
MALEFICS_NATURAL = {SU, MA, SA, RA, KE}

# Shadbala constants
NAISARGIKA_BALA = {SU: 60.0, MO: 51.43, VE: 42.86, JU: 34.29, ME: 25.71, MA: 17.14, SA: 8.57}
REQUIRED_SHADBALA_RUPAS = {SU: 5.0, MO: 6.0, MA: 5.0, ME: 7.0, JU: 6.5, VE: 5.5, SA: 5.0}
DISC_DIAMETERS = {MA: 9.4, ME: 6.6, JU: 190.4, VE: 16.6, SA: 158.0}

MALE_PLANETS = {SU, MA, JU}
NEUTER_PLANETS = {ME, SA}
FEMALE_PLANETS = {MO, VE}

# Sign types for bhava dig bala.
SHEERSHODAYA = {2, 4, 5, 6, 7, 10}
PRISHTODAYA = {0, 1, 3, 8, 9}
UBHAYODAYA = {11}
