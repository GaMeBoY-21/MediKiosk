// Owner: Ranjith
// Patient-facing names for the clinical fields the backend extracts, for the
// understanding panel only.
//
// Keys are the field names from ai/interview/nodes.py. Everyday words, not
// clinical vocabulary: the panel exists to let a patient recognise that the
// kiosk understood them, so "Where it hurts" beats "Site".
//
// A field with no entry here falls back to its own name, prettified. That is
// deliberate — a new backend field should show up looking slightly raw rather
// than vanish from the panel unnoticed.
//
// TRANSLATION NOTE: en and hi have been checked most carefully. The other five
// use common everyday terms but have not been reviewed by a native speaker —
// worth a pass before the judged demo.

import { t } from './strings.js';

const FIELD_NAMES = {
  patient_name: {
    en: 'Name', hi: 'नाम', kn: 'ಹೆಸರು', ta: 'பெயர்', te: 'పేరు', mr: 'नाव', bn: 'নাম',
  },
  age: {
    en: 'Age', hi: 'उम्र', kn: 'ವಯಸ್ಸು', ta: 'வயது', te: 'వయస్సు', mr: 'वय', bn: 'বয়স',
  },
  sex: {
    en: 'Sex', hi: 'लिंग', kn: 'ಲಿಂಗ', ta: 'பாலினம்', te: 'లింగం', mr: 'लिंग', bn: 'লিঙ্গ',
  },
  consent_given: {
    en: 'Consent', hi: 'सहमति', kn: 'ಒಪ್ಪಿಗೆ', ta: 'ஒப்புதல்', te: 'సమ్మతి', mr: 'संमती', bn: 'সম্মতি',
  },
  chief_complaint: {
    en: 'Problem', hi: 'तकलीफ़', kn: 'ತೊಂದರೆ', ta: 'பிரச்சனை', te: 'సమస్య', mr: 'त्रास', bn: 'সমস্যা',
  },
  symptom_duration: {
    en: 'Since', hi: 'कब से', kn: 'ಎಷ್ಟು ದಿನದಿಂದ', ta: 'எவ்வளவு காலம்', te: 'ఎంతకాలం', mr: 'किती दिवस', bn: 'কতদিন',
  },
  symptom_site: {
    en: 'Where', hi: 'कहाँ', kn: 'ಎಲ್ಲಿ', ta: 'எங்கே', te: 'ఎక్కడ', mr: 'कुठे', bn: 'কোথায়',
  },
  symptom_onset: {
    en: 'Started', hi: 'शुरुआत', kn: 'ಆರಂಭ', ta: 'தொடக்கம்', te: 'ప్రారంభం', mr: 'सुरुवात', bn: 'শুরু',
  },
  symptom_character: {
    en: 'Feels like', hi: 'कैसा लगता है', kn: 'ಹೇಗಿದೆ', ta: 'எப்படி உள்ளது', te: 'ఎలా ఉంది', mr: 'कसे वाटते', bn: 'কেমন লাগে',
  },
  symptom_severity: {
    en: 'How bad', hi: 'कितना तेज़', kn: 'ಎಷ್ಟು ತೀವ್ರ', ta: 'எவ்வளவு கடுமை', te: 'ఎంత తీవ్రం', mr: 'किती तीव्र', bn: 'কতটা তীব্র',
  },
  symptom_radiation: {
    en: 'Spreads to', hi: 'कहाँ तक फैलता है', kn: 'ಎಲ್ಲಿಗೆ ಹರಡುತ್ತದೆ', ta: 'எங்கு பரவுகிறது', te: 'ఎక్కడికి వ్యాపిస్తుంది', mr: 'कुठे पसरते', bn: 'কোথায় ছড়ায়',
  },
  symptom_timing: {
    en: 'When', hi: 'कब', kn: 'ಯಾವಾಗ', ta: 'எப்போது', te: 'ఎప్పుడు', mr: 'केव्हा', bn: 'কখন',
  },
  symptom_exacerbating_factors: {
    en: 'Worse with', hi: 'किससे बढ़ता है', kn: 'ಯಾವುದರಿಂದ ಹೆಚ್ಚಾಗುತ್ತದೆ', ta: 'எதனால் அதிகரிக்கும்', te: 'దేనితో ఎక్కువ', mr: 'कशाने वाढते', bn: 'কীসে বাড়ে',
  },
  symptom_relieving_factors: {
    en: 'Better with', hi: 'किससे आराम', kn: 'ಯಾವುದರಿಂದ ಆರಾಮ', ta: 'எதனால் நிவாரணம்', te: 'దేనితో ఉపశమనం', mr: 'कशाने आराम', bn: 'কীসে আরাম',
  },
  associated_symptoms: {
    en: 'Along with', hi: 'साथ में', kn: 'ಜೊತೆಗೆ', ta: 'உடன்', te: 'తోపాటు', mr: 'सोबत', bn: 'সঙ্গে',
  },
  ros_screen: {
    en: 'Other symptoms', hi: 'अन्य लक्षण', kn: 'ಇತರ ಲಕ್ಷಣಗಳು', ta: 'பிற அறிகுறிகள்', te: 'ఇతర లక్షణాలు', mr: 'इतर लक्षणे', bn: 'অন্যান্য লক্ষণ',
  },
  past_medical_conditions: {
    en: 'Past illness', hi: 'पुरानी बीमारी', kn: 'ಹಳೆಯ ಕಾಯಿಲೆ', ta: 'பழைய நோய்', te: 'పాత వ్యాధి', mr: 'जुना आजार', bn: 'পুরনো রোগ',
  },
  past_surgeries: {
    en: 'Operations', hi: 'ऑपरेशन', kn: 'ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ', ta: 'அறுவை சிகிச்சை', te: 'ఆపరేషన్', mr: 'ऑपरेशन', bn: 'অপারেশন',
  },
  current_medications: {
    en: 'Medicines', hi: 'दवाएँ', kn: 'ಔಷಧಿಗಳು', ta: 'மருந்துகள்', te: 'మందులు', mr: 'औषधे', bn: 'ওষুধ',
  },
  known_allergies: {
    en: 'Allergies', hi: 'एलर्जी', kn: 'ಅಲರ್ಜಿ', ta: 'ஒவ்வாமை', te: 'అలర్జీ', mr: 'ॲलर्जी', bn: 'অ্যালার্জি',
  },
  family_history: {
    en: 'Family', hi: 'परिवार', kn: 'ಕುಟುಂಬ', ta: 'குடும்பம்', te: 'కుటుంబం', mr: 'कुटुंब', bn: 'পরিবার',
  },
  smoking_status: {
    en: 'Smoking', hi: 'धूम्रपान', kn: 'ಧೂಮಪಾನ', ta: 'புகைப்பழக்கம்', te: 'ధూమపానం', mr: 'धूम्रपान', bn: 'ধূমপান',
  },
  alcohol_use: {
    en: 'Alcohol', hi: 'शराब', kn: 'ಮದ್ಯ', ta: 'மது', te: 'మద్యం', mr: 'दारू', bn: 'মদ',
  },
  diet: {
    en: 'Food', hi: 'खाना', kn: 'ಆಹಾರ', ta: 'உணவு', te: 'ఆహారం', mr: 'आहार', bn: 'খাবার',
  },
  occupation: {
    en: 'Work', hi: 'काम', kn: 'ಕೆಲಸ', ta: 'வேலை', te: 'పని', mr: 'काम', bn: 'কাজ',
  },
  sleep_pattern: {
    en: 'Sleep', hi: 'नींद', kn: 'ನಿದ್ರೆ', ta: 'தூக்கம்', te: 'నిద్ర', mr: 'झोप', bn: 'ঘুম',
  },
  documents_offered: {
    en: 'Reports', hi: 'रिपोर्ट', kn: 'ವರದಿಗಳು', ta: 'அறிக்கைகள்', te: 'నివేదికలు', mr: 'अहवाल', bn: 'রিপোর্ট',
  },
};

/** Prettify an unmapped field name rather than hiding it. */
function fallback(name) {
  return String(name).replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
}

export function fieldLabel(name, lang) {
  const entry = FIELD_NAMES[name];
  if (!entry) return fallback(name);
  return entry[lang] ?? entry.en ?? fallback(name);
}

/* ------------------------------------------------------- values, not names */

// The kiosk fills a handful of fields on its own screens — sex, consent, the
// body region — and posts the canonical value with no option list attached, so
// the API can only hand back the value opened out ("Male"). The translated
// string does exist: it is the label that was on the tile the patient tapped.
// This maps those canonical values back to it.
//
// Deliberately a closed set. Everything else the patient answers goes through
// the interview, where the API returns the label it generated in their
// language, and guessing at values beyond this list would mean inventing
// translations for clinical content that the model already writes correctly.
const VALUE_KEYS = {
  sex: { male: 'identify.male', female: 'identify.female', other: 'identify.otherSex' },
  consent_given: { true: 'common.yes', false: 'common.no', yes: 'common.yes', no: 'common.no' },
  chief_complaint: Object.fromEntries(
    ['head', 'chest', 'stomach', 'back', 'joints', 'skin', 'fever', 'breathing', 'other'].map(
      (a) => [a, `complaint.${a}`],
    ),
  ),
};
// The body region is derived from the same tiles, so it reads the same labels.
VALUE_KEYS.symptom_site = VALUE_KEYS.chief_complaint;

/**
 * Patient-language label for a canonical value, or undefined when this is not
 * one of the values the kiosk itself collected.
 *
 * @param {string} name   field name, e.g. 'sex'
 * @param {*} value       canonical value, e.g. 'male'
 * @param {string} lang   language code
 */
export function valueLabel(name, value, lang) {
  if (value === null || value === undefined || Array.isArray(value)) return undefined;
  const path = VALUE_KEYS[name]?.[String(value)];
  return path ? t(lang, path).label : undefined;
}
