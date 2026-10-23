// Hindi names for astrology terms returned (in English) by the backend.
// Keys are exactly the backend's values; anything missing falls back to English.

export const PLANET_CODES = ['Su', 'Mo', 'Ma', 'Me', 'Ju', 'Ve', 'Sa', 'Ra', 'Ke'];

export const GLYPH = { Su: '☉', Mo: '☽', Ma: '♂', Me: '☿', Ju: '♃', Ve: '♀', Sa: '♄', Ra: '☊', Ke: '☋' };

// English UI keeps Sanskrit terms in everyday Hinglish spelling (no diacritics), e.g. "Budh", "Rashi".
// Anything not listed falls through as the backend's plain spelling.
const en = {
  graha: { Su: 'Surya', Mo: 'Chandra', Ma: 'Mangal', Me: 'Budh', Ju: 'Guru', Ve: 'Shukra', Sa: 'Shani', Ra: 'Rahu', Ke: 'Ketu' },
  grahaFull: {
    Su: 'Surya · Sun', Mo: 'Chandra · Moon', Ma: 'Mangal · Mars', Me: 'Budh · Mercury', Ju: 'Guru · Jupiter',
    Ve: 'Shukra · Venus', Sa: 'Shani · Saturn', Ra: 'Rahu · North node', Ke: 'Ketu · South node',
  },
  planet: { Su: 'Sun', Mo: 'Moon', Ma: 'Mars', Me: 'Mercury', Ju: 'Jupiter', Ve: 'Venus', Sa: 'Saturn', Ra: 'Rahu', Ke: 'Ketu' },
  planetShort: { Su: 'Su', Mo: 'Mo', Ma: 'Ma', Me: 'Me', Ju: 'Ju', Ve: 'Ve', Sa: 'Sa', Ra: 'Ra', Ke: 'Ke' },
  month: { Ashwin: 'Ashwin', Shravana: 'Shravan', Vaishakha: 'Vaishakh', Ashadha: 'Ashadh', Kartika: 'Kartik', Margashirsha: 'Margashirsh', Pausha: 'Paush', Magha: 'Magh', Phalguna: 'Phalgun' },
  varga: { Rasi: 'Rashi' },
  dignity: {
    exalted: 'Exalted', debilitated: 'Debilitated', moolatrikona: 'Moolatrikona', own: 'Own sign',
    great_friend: 'Great friend', friend: 'Friend', neutral: 'Neutral', enemy: 'Enemy', great_enemy: 'Great enemy',
  },
};

const hi = {
  graha: { Su: 'सूर्य', Mo: 'चंद्र', Ma: 'मंगल', Me: 'बुध', Ju: 'गुरु', Ve: 'शुक्र', Sa: 'शनि', Ra: 'राहु', Ke: 'केतु' },
  grahaFull: { Su: 'सूर्य', Mo: 'चंद्र', Ma: 'मंगल', Me: 'बुध', Ju: 'गुरु', Ve: 'शुक्र', Sa: 'शनि', Ra: 'राहु', Ke: 'केतु' },
  planet: { Su: 'सूर्य', Mo: 'चंद्र', Ma: 'मंगल', Me: 'बुध', Ju: 'गुरु', Ve: 'शुक्र', Sa: 'शनि', Ra: 'राहु', Ke: 'केतु' },
  planetShort: { Su: 'सू', Mo: 'चं', Ma: 'मं', Me: 'बु', Ju: 'गु', Ve: 'शु', Sa: 'श', Ra: 'रा', Ke: 'के' },
  sign: {
    Aries: 'मेष', Taurus: 'वृषभ', Gemini: 'मिथुन', Cancer: 'कर्क', Leo: 'सिंह', Virgo: 'कन्या',
    Libra: 'तुला', Scorpio: 'वृश्चिक', Sagittarius: 'धनु', Capricorn: 'मकर', Aquarius: 'कुंभ', Pisces: 'मीन',
  },
  nakshatra: {
    Ashwini: 'अश्विनी', Bharani: 'भरणी', Krittika: 'कृत्तिका', Rohini: 'रोहिणी', Mrigashira: 'मृगशिरा',
    Ardra: 'आर्द्रा', Punarvasu: 'पुनर्वसु', Pushya: 'पुष्य', Ashlesha: 'आश्लेषा', Magha: 'मघा',
    'Purva Phalguni': 'पूर्व फाल्गुनी', 'Uttara Phalguni': 'उत्तर फाल्गुनी', Hasta: 'हस्त', Chitra: 'चित्रा',
    Swati: 'स्वाति', Vishakha: 'विशाखा', Anuradha: 'अनुराधा', Jyeshtha: 'ज्येष्ठा', Mula: 'मूल',
    'Purva Ashadha': 'पूर्वाषाढ़ा', 'Uttara Ashadha': 'उत्तराषाढ़ा', Shravana: 'श्रवण', Dhanishta: 'धनिष्ठा',
    Shatabhisha: 'शतभिषा', 'Purva Bhadrapada': 'पूर्व भाद्रपद', 'Uttara Bhadrapada': 'उत्तर भाद्रपद', Revati: 'रेवती',
  },
  tithi: {
    Pratipada: 'प्रतिपदा', Dwitiya: 'द्वितीया', Tritiya: 'तृतीया', Chaturthi: 'चतुर्थी', Panchami: 'पंचमी',
    Shashthi: 'षष्ठी', Saptami: 'सप्तमी', Ashtami: 'अष्टमी', Navami: 'नवमी', Dashami: 'दशमी',
    Ekadashi: 'एकादशी', Dwadashi: 'द्वादशी', Trayodashi: 'त्रयोदशी', Chaturdashi: 'चतुर्दशी',
    Purnima: 'पूर्णिमा', Amavasya: 'अमावस्या',
  },
  paksha: { Shukla: 'शुक्ल', Krishna: 'कृष्ण' },
  yoga: {
    Vishkambha: 'विष्कुम्भ', Priti: 'प्रीति', Ayushman: 'आयुष्मान', Saubhagya: 'सौभाग्य', Shobhana: 'शोभन',
    Atiganda: 'अतिगण्ड', Sukarma: 'सुकर्मा', Dhriti: 'धृति', Shula: 'शूल', Ganda: 'गण्ड', Vriddhi: 'वृद्धि',
    Dhruva: 'ध्रुव', Vyaghata: 'व्याघात', Harshana: 'हर्षण', Vajra: 'वज्र', Siddhi: 'सिद्धि',
    Vyatipata: 'व्यतीपात', Variyan: 'वरीयान', Parigha: 'परिघ', Shiva: 'शिव', Siddha: 'सिद्ध',
    Sadhya: 'साध्य', Shubha: 'शुभ', Shukla: 'शुक्ल', Brahma: 'ब्रह्म', Indra: 'इन्द्र', Vaidhriti: 'वैधृति',
  },
  karana: {
    Bava: 'बव', Balava: 'बालव', Kaulava: 'कौलव', Taitila: 'तैतिल', Gara: 'गर', Vanija: 'वणिज',
    Vishti: 'विष्टि (भद्रा)', Shakuni: 'शकुनि', Chatushpada: 'चतुष्पद', Naga: 'नाग', Kimstughna: 'किंस्तुघ्न',
  },
  weekday: {
    Sunday: 'रविवार', Monday: 'सोमवार', Tuesday: 'मंगलवार', Wednesday: 'बुधवार', Thursday: 'गुरुवार',
    Friday: 'शुक्रवार', Saturday: 'शनिवार',
  },
  month: {
    Chaitra: 'चैत्र', Vaishakha: 'वैशाख', Jyeshtha: 'ज्येष्ठ', Ashadha: 'आषाढ़', Shravana: 'श्रावण',
    Bhadrapada: 'भाद्रपद', Ashwin: 'आश्विन', Kartika: 'कार्तिक', Margashirsha: 'मार्गशीर्ष', Pausha: 'पौष',
    Magha: 'माघ', Phalguna: 'फाल्गुन',
  },
  ayana: { Uttarayana: 'उत्तरायण', Dakshinayana: 'दक्षिणायन' },
  dignity: {
    exalted: 'उच्च', debilitated: 'नीच', moolatrikona: 'मूलत्रिकोण', own: 'स्वगृही',
    great_friend: 'अधिमित्र', friend: 'मित्र', neutral: 'सम', enemy: 'शत्रु', great_enemy: 'अधिशत्रु',
  },
  avastha: {
    Bala: 'बाल', Kumara: 'कुमार', Yuva: 'युवा', Vriddha: 'वृद्ध', Mrita: 'मृत',
    Jagrat: 'जाग्रत', Swapna: 'स्वप्न', Sushupti: 'सुषुप्ति',
  },
  dashaLevel: {
    mahadasha: 'महादशा', antardasha: 'अंतर्दशा', pratyantardasha: 'प्रत्यंतर्दशा', sookshma: 'सूक्ष्म', prana: 'प्राण',
  },
  varga: {
    Rasi: 'राशि', Hora: 'होरा', Drekkana: 'द्रेष्काण', Chaturthamsa: 'चतुर्थांश', Saptamsa: 'सप्तमांश',
    Navamsa: 'नवमांश', Dasamsa: 'दशमांश', Dwadasamsa: 'द्वादशांश', Shodasamsa: 'षोडशांश', Vimsamsa: 'विंशांश',
    Chaturvimsamsa: 'चतुर्विंशांश', Saptavimsamsa: 'सप्तविंशांश', Trimsamsa: 'त्रिंशांश', Khavedamsa: 'खवेदांश',
    Akshavedamsa: 'अक्षवेदांश', Shashtiamsa: 'षष्ट्यंश',
  },
  avakhada: {
    // varna, vashya, yoni, gana, nadi, tatva, paya values
    Brahmin: 'ब्राह्मण', Kshatriya: 'क्षत्रिय', Vaishya: 'वैश्य', Shudra: 'शूद्र',
    Chatushpada: 'चतुष्पद', Manava: 'मानव', Jalachara: 'जलचर', Vanachara: 'वनचर', Keeta: 'कीट',
    Horse: 'अश्व', Elephant: 'गज', Sheep: 'मेष', Serpent: 'सर्प', Dog: 'श्वान', Cat: 'मार्जार', Rat: 'मूषक',
    Cow: 'गौ', Buffalo: 'महिष', Tiger: 'व्याघ्र', Deer: 'मृग', Monkey: 'वानर', Mongoose: 'नकुल', Lion: 'सिंह',
    Deva: 'देव', Manushya: 'मनुष्य', Rakshasa: 'राक्षस',
    Adi: 'आदि', Madhya: 'मध्य', Antya: 'अन्त्य',
    Fire: 'अग्नि', Earth: 'पृथ्वी', Air: 'वायु', Water: 'जल',
    'Swarna (Gold)': 'स्वर्ण', 'Rajat (Silver)': 'रजत', 'Tamra (Copper)': 'ताम्र', 'Loha (Iron)': 'लौह',
  },
};

const dictionaries = { en, hi };

/** Translate a backend term. `category` is a key above, `value` the backend string/code. */
export function term(lang, category, value) {
  if (value === null || value === undefined) return '';
  const dict = dictionaries[lang]?.[category];
  if (dict && dict[value]) return dict[value];
  if (en[category]?.[value]) return en[category][value];
  if (category === 'avakhada' && lang === 'hi') {
    // signs, planets and nakshatras also appear inside avakhada
    return hi.sign[value] || hi.nakshatra[value] || hi.planet[value] || value;
  }
  return String(value).replace(/_/g, ' ');
}
