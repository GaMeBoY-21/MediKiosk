// Owner: Ranjith
// Every user-facing string, keyed by screen, in all seven languages.
//
// Each entry is { label, audio }:
//   label — what appears on screen, kept short so it survives 40px type
//   audio — what is spoken, usually a longer, friendlier full sentence
// Text is the backup for the audio, not the other way round.
//
// Clinical content is NOT here. Interview questions come from the API.

export const LANGUAGES = [
  { code: 'en', native: 'English', bcp47: 'en-IN' },
  { code: 'hi', native: 'हिन्दी', bcp47: 'hi-IN' },
  { code: 'kn', native: 'ಕನ್ನಡ', bcp47: 'kn-IN' },
  { code: 'ta', native: 'தமிழ்', bcp47: 'ta-IN' },
  { code: 'te', native: 'తెలుగు', bcp47: 'te-IN' },
  { code: 'mr', native: 'मराठी', bcp47: 'mr-IN' },
  { code: 'bn', native: 'বাংলা', bcp47: 'bn-IN' },
];

export const DEFAULT_LANG = 'en';

export function bcp47(code) {
  return (LANGUAGES.find((l) => l.code === code) || LANGUAGES[0]).bcp47;
}

export const strings = {
  en: {
    // Stage labels. The API sends only the key (e.g. 'hpi'); these are static
    // UI chrome, so they belong here with the other static strings rather than
    // as English prose inside a clinical file.
    phase: {
      identity: { label: 'Let\'s start with a few basic details.', audio: '' },
      consent: { label: 'Before we begin, we need your consent.', audio: '' },
      chief_complaint: { label: 'What brings you in today?', audio: '' },
      hpi: { label: 'Tell me more about this problem.', audio: '' },
      ros: { label: 'One quick question about how you\'ve been feeling overall.', audio: '' },
      past_medical: { label: 'Do you have any ongoing health conditions or past surgeries?', audio: '' },
      drug_allergy: { label: 'Are you taking any medicines, and do you have any allergies?', audio: '' },
      family: { label: 'Does anyone in your immediate family have a serious illness?', audio: '' },
      personal: { label: 'A few lifestyle questions.', audio: '' },
      documents: { label: 'Do you have any prior prescriptions or lab reports to show us?', audio: '' },
      confirm: { label: 'Please review your answers before we finish.', audio: '' },
    },
    common: {
      repeat: { label: 'Repeat', audio: 'Listen to that again.' },
      listen: { label: 'Listen', audio: '' },
      stop: { label: 'Stop', audio: '' },
      back: { label: 'Back', audio: 'Going back.' },
      next: { label: 'Next', audio: 'Next question.' },
      yes: { label: 'Yes', audio: 'Yes.' },
      no: { label: 'No', audio: 'No.' },
      doneSpeaking: { label: 'Done speaking', audio: 'Finished speaking.' },
      tapToSpeak: { label: 'Tap to speak', audio: 'Tap the green circle and speak.' },
      tapOrType: {
        label: 'Tap the mic to speak, or type here',
        audio: 'Tap the green circle and speak, or type your answer here.',
      },
      typeHere: {
        label: 'Type your answer here',
        audio: 'The microphone is not working. Please type your answer here.',
      },
      listening: { label: 'Listening', audio: 'I am listening.' },
      oneMoment: { label: 'One moment', audio: 'One moment please.' },
      understood: { label: 'What we understood', audio: '' },
      moreFields: { label: '+{n} more', audio: '' },
      notSure: { label: 'Not sure — please check', audio: '' },
      edit: { label: 'Edit', audio: 'Change this answer.' },
      micUnavailable: {
        label: 'You can tap your answer instead',
        audio: 'The microphone is not working. Please tap your answer instead.',
      },
    },
    idle: {
      begin: { label: 'Touch here to begin', audio: 'Touch the screen to begin.' },
      subtitle: { label: 'Ministry of Ayush · Out-Patient Department', audio: '' },
    },
    language: {
      title: { label: 'Choose your language', audio: 'Please choose your language.' },
      greeting: { label: 'English', audio: 'English selected. Let us begin.' },
    },
    identify: {
      title: { label: 'Let us find your records', audio: 'Let us find your records. Please choose one.' },
      abha: { label: 'I have an ABHA number', audio: 'I have an ABHA number.' },
      aadhaar: { label: 'I have Aadhaar', audio: 'I have an Aadhaar number.' },
      newHere: { label: 'I am new here', audio: 'I am new here.' },
      abhaTitle: { label: 'Enter your ABHA number', audio: 'Please type your ABHA number using the number keys.' },
      aadhaarTitle: { label: 'Enter your Aadhaar number', audio: 'Please type your Aadhaar number using the number keys.' },
      checking: { label: 'Checking', audio: 'Checking your number. One moment.' },
      nameTitle: { label: 'What is your name?', audio: 'What is your name? You may speak it or type it.' },
      ageTitle: { label: 'What is your age?', audio: 'What is your age? Please type it using the number keys.' },
      sexTitle: { label: 'Please choose', audio: 'Please choose one.' },
      male: { label: 'Male', audio: 'Male.' },
      female: { label: 'Female', audio: 'Female.' },
      otherSex: { label: 'Other', audio: 'Other.' },
    },
    consent: {
      title: { label: 'Your permission', audio: '' },
      explanation: {
        label:
          'This kiosk will ask you questions about your health and record your answers in your own voice. It may also read photographs of your old prescriptions and reports. Only the doctor who sees you today will read this. Nothing is shared with anyone else. You may refuse. If you refuse, you can still meet the doctor in the normal way.',
        audio:
          'Please listen carefully. This kiosk will ask you questions about your health and record your answers in your own voice. It may also read photographs of your old prescriptions and reports. Only the doctor who sees you today will read this information. Nothing is shared with anyone else. You may refuse. If you refuse, you can still meet the doctor in the normal way.',
      },
      playAgain: { label: 'Play again', audio: '' },
      optHistory: { label: 'Record my medical history', audio: 'Record my medical history.' },
      optDocuments: { label: 'Read my old medical documents', audio: 'Read my old medical documents.' },
      optAbha: { label: 'Link this to my ABHA health record', audio: 'Link this to my ABHA health record.' },
      agree: { label: 'I agree', audio: 'I agree.' },
      decline: { label: 'I do not agree', audio: 'I do not agree.' },
      declinedTitle: { label: 'That is all right', audio: 'That is all right.' },
      declinedBody: {
        label: 'You can still see the doctor in the usual way. Please go to the counter.',
        audio: 'You can still see the doctor in the usual way. Please go to the counter.',
      },
    },
    complaint: {
      title: { label: 'What is troubling you today?', audio: 'What is troubling you today? You may speak, or tap a picture.' },
      head: { label: 'Head', audio: 'Head.' },
      chest: { label: 'Chest', audio: 'Chest.' },
      stomach: { label: 'Stomach', audio: 'Stomach.' },
      back: { label: 'Back', audio: 'Back.' },
      joints: { label: 'Joints', audio: 'Joints.' },
      skin: { label: 'Skin', audio: 'Skin.' },
      fever: { label: 'Fever', audio: 'Fever.' },
      breathing: { label: 'Breathing', audio: 'Breathing.' },
      other: { label: 'Something else', audio: 'Something else.' },
    },
    documents: {
      title: { label: 'Do you have any old prescriptions or reports?', audio: 'Do you have any old prescriptions or reports with you today?' },
      yes: { label: 'Yes, I have papers', audio: 'Yes, I have papers.' },
      no: { label: 'No, skip this', audio: 'No, skip this.' },
      cameraTitle: { label: 'Hold the paper inside the box', audio: 'Hold the paper flat inside the box, then press the round button.' },
      capture: { label: 'Take photo', audio: 'Take photo.' },
      addAnother: { label: 'Add another', audio: 'Add another paper.' },
      done: { label: 'Done', audio: 'Finished.' },
      remove: { label: 'Remove', audio: 'Removed.' },
      cameraBlocked: {
        label: 'The camera is not available. Please show your papers to the doctor.',
        audio: 'The camera is not available. Please show your papers to the doctor.',
      },
    },
    confirm: {
      title: { label: 'Please check what you told us', audio: 'Please listen and check what you told us.' },
      correct: { label: 'Yes, this is correct', audio: 'Yes, this is correct.' },
      nothing: { label: 'Nothing was recorded', audio: 'Nothing was recorded.' },
    },
    done: {
      title: { label: 'Thank you', audio: 'Thank you.' },
      token: { label: 'Your token number', audio: '' },
      room: { label: "Doctor's room", audio: '' },
      wait: { label: 'Please wait. You will be called.', audio: 'Please wait. You will be called.' },
    },
    emergency: {
      patient: { label: 'Please go to the emergency counter now', audio: 'Please go to the emergency counter now. Show this screen to the staff.' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'Are you still there?', audio: 'Are you still there?' },
      continue: { label: 'Yes, continue', audio: 'Yes, continue.' },
      closing: { label: 'Closing in', audio: '' },
    },
    error: {
      title: { label: 'Something went wrong', audio: 'Something went wrong. Please call a staff member.' },
      body: { label: 'Please call a staff member.', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'Start again', audio: '' },
    },
  },

  hi: {
    phase: {
      identity: { label: 'आइए कुछ बुनियादी जानकारी से शुरू करें।', audio: '' },
      consent: { label: 'शुरू करने से पहले हमें आपकी सहमति चाहिए।', audio: '' },
      chief_complaint: { label: 'आज आप किस समस्या के लिए आए हैं?', audio: '' },
      hpi: { label: 'इस समस्या के बारे में और बताइए।', audio: '' },
      ros: { label: 'आपकी कुल सेहत के बारे में एक छोटा सवाल।', audio: '' },
      past_medical: { label: 'क्या आपको कोई पुरानी बीमारी है या कोई ऑपरेशन हुआ है?', audio: '' },
      drug_allergy: { label: 'क्या आप कोई दवा लेते हैं, और क्या कोई एलर्जी है?', audio: '' },
      family: { label: 'क्या आपके परिवार में किसी को गंभीर बीमारी है?', audio: '' },
      personal: { label: 'जीवनशैली से जुड़े कुछ सवाल।', audio: '' },
      documents: { label: 'क्या आपके पास पुराने पर्चे या जाँच रिपोर्ट हैं?', audio: '' },
      confirm: { label: 'खत्म करने से पहले अपने जवाब देख लीजिए।', audio: '' },
    },
    common: {
      repeat: { label: 'फिर से सुनें', audio: 'इसे फिर से सुनिए।' },
      listen: { label: 'सुनें', audio: '' },
      stop: { label: 'रोकें', audio: '' },
      back: { label: 'पीछे', audio: 'पीछे जा रहे हैं।' },
      next: { label: 'आगे', audio: 'अगला सवाल।' },
      yes: { label: 'हाँ', audio: 'हाँ।' },
      no: { label: 'नहीं', audio: 'नहीं।' },
      doneSpeaking: { label: 'बोलना पूरा हुआ', audio: 'बोलना पूरा हुआ।' },
      tapToSpeak: { label: 'बोलने के लिए दबाएँ', audio: 'हरे गोले को दबाइए और बोलिए।' },
      tapOrType: {
        label: 'बोलने के लिए माइक दबाएँ, या यहाँ लिखें',
        audio: 'हरे गोले को दबाकर बोलिए, या अपना जवाब यहाँ लिखिए।',
      },
      typeHere: {
        label: 'अपना जवाब यहाँ लिखें',
        audio: 'माइक काम नहीं कर रहा। कृपया अपना जवाब यहाँ लिखिए।',
      },
      listening: { label: 'सुन रहे हैं', audio: 'मैं सुन रहा हूँ।' },
      oneMoment: { label: 'एक क्षण', audio: 'कृपया एक क्षण रुकिए।' },
      understood: { label: 'हमने क्या समझा', audio: '' },
      moreFields: { label: '+{n} और', audio: '' },
      notSure: { label: 'पक्का नहीं — कृपया जाँचें', audio: '' },
      edit: { label: 'बदलें', audio: 'यह जवाब बदलिए।' },
      micUnavailable: {
        label: 'आप अपना जवाब दबाकर भी चुन सकते हैं',
        audio: 'माइक काम नहीं कर रहा। कृपया अपना जवाब दबाकर चुनिए।',
      },
    },
    idle: {
      begin: { label: 'शुरू करने के लिए यहाँ छुएँ', audio: 'शुरू करने के लिए स्क्रीन को छुइए।' },
      subtitle: { label: 'आयुष मंत्रालय · बाह्य रोगी विभाग', audio: '' },
    },
    language: {
      title: { label: 'अपनी भाषा चुनें', audio: 'कृपया अपनी भाषा चुनिए।' },
      greeting: { label: 'हिन्दी', audio: 'नमस्ते। हिन्दी चुनी गई है। आइए शुरू करें।' },
    },
    identify: {
      title: { label: 'आइए आपका रिकॉर्ड ढूँढें', audio: 'आइए आपका रिकॉर्ड ढूँढें। कृपया एक विकल्प चुनिए।' },
      abha: { label: 'मेरे पास आभा नंबर है', audio: 'मेरे पास आभा नंबर है।' },
      aadhaar: { label: 'मेरे पास आधार है', audio: 'मेरे पास आधार नंबर है।' },
      newHere: { label: 'मैं यहाँ नया हूँ', audio: 'मैं यहाँ नया हूँ।' },
      abhaTitle: { label: 'अपना आभा नंबर दर्ज करें', audio: 'कृपया अंकों की मदद से अपना आभा नंबर लिखिए।' },
      aadhaarTitle: { label: 'अपना आधार नंबर दर्ज करें', audio: 'कृपया अंकों की मदद से अपना आधार नंबर लिखिए।' },
      checking: { label: 'जाँच हो रही है', audio: 'आपका नंबर जाँचा जा रहा है। एक क्षण।' },
      nameTitle: { label: 'आपका नाम क्या है?', audio: 'आपका नाम क्या है? आप बोल सकते हैं या लिख सकते हैं।' },
      ageTitle: { label: 'आपकी उम्र क्या है?', audio: 'आपकी उम्र क्या है? कृपया अंकों से लिखिए।' },
      sexTitle: { label: 'कृपया चुनें', audio: 'कृपया एक चुनिए।' },
      male: { label: 'पुरुष', audio: 'पुरुष।' },
      female: { label: 'महिला', audio: 'महिला।' },
      otherSex: { label: 'अन्य', audio: 'अन्य।' },
    },
    consent: {
      title: { label: 'आपकी अनुमति', audio: '' },
      explanation: {
        label:
          'यह मशीन आपसे आपकी सेहत के बारे में सवाल पूछेगी और आपके जवाब आपकी आवाज़ में दर्ज करेगी। यह आपकी पुरानी पर्चियों और रिपोर्टों की तस्वीरें भी पढ़ सकती है। यह जानकारी केवल वही डॉक्टर देखेंगे जो आज आपको देखेंगे। किसी और के साथ कुछ साझा नहीं किया जाएगा। आप मना कर सकते हैं। मना करने पर भी आप सामान्य तरीके से डॉक्टर से मिल सकते हैं।',
        audio:
          'कृपया ध्यान से सुनिए। यह मशीन आपसे आपकी सेहत के बारे में सवाल पूछेगी और आपके जवाब आपकी आवाज़ में दर्ज करेगी। यह आपकी पुरानी पर्चियों और रिपोर्टों की तस्वीरें भी पढ़ सकती है। यह जानकारी केवल वही डॉक्टर देखेंगे जो आज आपको देखेंगे। किसी और के साथ कुछ साझा नहीं किया जाएगा। आप मना कर सकते हैं। मना करने पर भी आप सामान्य तरीके से डॉक्टर से मिल सकते हैं।',
      },
      playAgain: { label: 'फिर से सुनें', audio: '' },
      optHistory: { label: 'मेरा स्वास्थ्य विवरण दर्ज करें', audio: 'मेरा स्वास्थ्य विवरण दर्ज करें।' },
      optDocuments: { label: 'मेरे पुराने कागज़ पढ़ें', audio: 'मेरे पुराने कागज़ पढ़ें।' },
      optAbha: { label: 'इसे मेरे आभा रिकॉर्ड से जोड़ें', audio: 'इसे मेरे आभा रिकॉर्ड से जोड़ें।' },
      agree: { label: 'मैं सहमत हूँ', audio: 'मैं सहमत हूँ।' },
      decline: { label: 'मैं सहमत नहीं हूँ', audio: 'मैं सहमत नहीं हूँ।' },
      declinedTitle: { label: 'कोई बात नहीं', audio: 'कोई बात नहीं।' },
      declinedBody: {
        label: 'आप सामान्य तरीके से डॉक्टर से मिल सकते हैं। कृपया काउंटर पर जाएँ।',
        audio: 'आप सामान्य तरीके से डॉक्टर से मिल सकते हैं। कृपया काउंटर पर जाएँ।',
      },
    },
    complaint: {
      title: { label: 'आज आपको क्या तकलीफ़ है?', audio: 'आज आपको क्या तकलीफ़ है? आप बोल सकते हैं, या तस्वीर दबा सकते हैं।' },
      head: { label: 'सिर', audio: 'सिर।' },
      chest: { label: 'छाती', audio: 'छाती।' },
      stomach: { label: 'पेट', audio: 'पेट।' },
      back: { label: 'पीठ', audio: 'पीठ।' },
      joints: { label: 'जोड़', audio: 'जोड़।' },
      skin: { label: 'त्वचा', audio: 'त्वचा।' },
      fever: { label: 'बुखार', audio: 'बुखार।' },
      breathing: { label: 'साँस', audio: 'साँस।' },
      other: { label: 'कुछ और', audio: 'कुछ और।' },
    },
    documents: {
      title: { label: 'क्या आपके पास पुरानी पर्ची या रिपोर्ट है?', audio: 'क्या आज आपके पास पुरानी पर्ची या रिपोर्ट है?' },
      yes: { label: 'हाँ, मेरे पास कागज़ हैं', audio: 'हाँ, मेरे पास कागज़ हैं।' },
      no: { label: 'नहीं, आगे बढ़ें', audio: 'नहीं, आगे बढ़ें।' },
      cameraTitle: { label: 'कागज़ को डिब्बे के अंदर रखें', audio: 'कागज़ को सीधा करके डिब्बे के अंदर रखिए, फिर गोल बटन दबाइए।' },
      capture: { label: 'फ़ोटो लें', audio: 'फ़ोटो लें।' },
      addAnother: { label: 'एक और जोड़ें', audio: 'एक और कागज़ जोड़ें।' },
      done: { label: 'पूरा हुआ', audio: 'पूरा हुआ।' },
      remove: { label: 'हटाएँ', audio: 'हटा दिया।' },
      cameraBlocked: {
        label: 'कैमरा उपलब्ध नहीं है। कृपया अपने कागज़ डॉक्टर को दिखाएँ।',
        audio: 'कैमरा उपलब्ध नहीं है। कृपया अपने कागज़ डॉक्टर को दिखाएँ।',
      },
    },
    confirm: {
      title: { label: 'आपने जो बताया उसे जाँच लें', audio: 'कृपया सुनिए और जाँचिए कि आपने क्या बताया।' },
      correct: { label: 'हाँ, यह सही है', audio: 'हाँ, यह सही है।' },
      nothing: { label: 'कुछ दर्ज नहीं हुआ', audio: 'कुछ दर्ज नहीं हुआ।' },
    },
    done: {
      title: { label: 'धन्यवाद', audio: 'धन्यवाद।' },
      token: { label: 'आपका टोकन नंबर', audio: '' },
      room: { label: 'डॉक्टर का कमरा', audio: '' },
      wait: { label: 'कृपया प्रतीक्षा करें। आपको बुलाया जाएगा।', audio: 'कृपया प्रतीक्षा करें। आपको बुलाया जाएगा।' },
    },
    emergency: {
      patient: { label: 'कृपया अभी आपातकालीन काउंटर पर जाएँ', audio: 'कृपया अभी आपातकालीन काउंटर पर जाएँ। यह स्क्रीन कर्मचारी को दिखाएँ।' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'क्या आप अब भी यहाँ हैं?', audio: 'क्या आप अब भी यहाँ हैं?' },
      continue: { label: 'हाँ, जारी रखें', audio: 'हाँ, जारी रखें।' },
      closing: { label: 'बंद हो रहा है', audio: '' },
    },
    error: {
      title: { label: 'कुछ गड़बड़ हो गई', audio: 'कुछ गड़बड़ हो गई। कृपया कर्मचारी को बुलाएँ।' },
      body: { label: 'कृपया कर्मचारी को बुलाएँ।', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'फिर से शुरू करें', audio: '' },
    },
  },

  kn: {
    phase: {
      identity: { label: 'ಕೆಲವು ಮೂಲ ವಿವರಗಳಿಂದ ಆರಂಭಿಸೋಣ.', audio: '' },
      consent: { label: 'ಆರಂಭಿಸುವ ಮೊದಲು ನಿಮ್ಮ ಒಪ್ಪಿಗೆ ಬೇಕು.', audio: '' },
      chief_complaint: { label: 'ಇಂದು ನಿಮಗೆ ಏನು ತೊಂದರೆ?', audio: '' },
      hpi: { label: 'ಈ ಸಮಸ್ಯೆಯ ಬಗ್ಗೆ ಇನ್ನಷ್ಟು ಹೇಳಿ.', audio: '' },
      ros: { label: 'ನಿಮ್ಮ ಒಟ್ಟಾರೆ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಒಂದು ಸಣ್ಣ ಪ್ರಶ್ನೆ.', audio: '' },
      past_medical: { label: 'ನಿಮಗೆ ದೀರ್ಘಕಾಲದ ಕಾಯಿಲೆ ಅಥವಾ ಹಿಂದೆ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಆಗಿದೆಯೆ?', audio: '' },
      drug_allergy: { label: 'ನೀವು ಯಾವುದೇ ಔಷಧಿ ತೆಗೆದುಕೊಳ್ಳುತ್ತೀರಾ, ಅಲರ್ಜಿ ಇದೆಯೆ?', audio: '' },
      family: { label: 'ನಿಮ್ಮ ಕುಟುಂಬದಲ್ಲಿ ಯಾರಿಗಾದರೂ ಗಂಭೀರ ಕಾಯಿಲೆ ಇದೆಯೆ?', audio: '' },
      personal: { label: 'ಜೀವನಶೈಲಿಯ ಕೆಲವು ಪ್ರಶ್ನೆಗಳು.', audio: '' },
      documents: { label: 'ನಿಮ್ಮ ಬಳಿ ಹಳೆಯ ಚೀಟಿ ಅಥವಾ ಪರೀಕ್ಷಾ ವರದಿ ಇದೆಯೆ?', audio: '' },
      confirm: { label: 'ಮುಗಿಸುವ ಮೊದಲು ನಿಮ್ಮ ಉತ್ತರಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.', audio: '' },
    },
    common: {
      repeat: { label: 'ಮತ್ತೆ ಕೇಳಿ', audio: 'ಇದನ್ನು ಮತ್ತೆ ಕೇಳಿ.' },
      listen: { label: 'ಕೇಳಿ', audio: '' },
      stop: { label: 'ನಿಲ್ಲಿಸಿ', audio: '' },
      back: { label: 'ಹಿಂದೆ', audio: 'ಹಿಂದೆ ಹೋಗುತ್ತಿದ್ದೇವೆ.' },
      next: { label: 'ಮುಂದೆ', audio: 'ಮುಂದಿನ ಪ್ರಶ್ನೆ.' },
      yes: { label: 'ಹೌದು', audio: 'ಹೌದು.' },
      no: { label: 'ಇಲ್ಲ', audio: 'ಇಲ್ಲ.' },
      doneSpeaking: { label: 'ಮಾತು ಮುಗಿಯಿತು', audio: 'ಮಾತು ಮುಗಿಯಿತು.' },
      tapToSpeak: { label: 'ಮಾತನಾಡಲು ಒತ್ತಿ', audio: 'ಹಸಿರು ವೃತ್ತವನ್ನು ಒತ್ತಿ ಮಾತನಾಡಿ.' },
      tapOrType: {
        label: 'ಮಾತನಾಡಲು ಮೈಕ್ ಒತ್ತಿ, ಅಥವಾ ಇಲ್ಲಿ ಬರೆಯಿರಿ',
        audio: 'ಹಸಿರು ವೃತ್ತವನ್ನು ಒತ್ತಿ ಮಾತನಾಡಿ, ಅಥವಾ ನಿಮ್ಮ ಉತ್ತರವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ.',
      },
      typeHere: {
        label: 'ನಿಮ್ಮ ಉತ್ತರವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ',
        audio: 'ಮೈಕ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಉತ್ತರವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ.',
      },
      listening: { label: 'ಕೇಳುತ್ತಿದೆ', audio: 'ನಾನು ಕೇಳುತ್ತಿದ್ದೇನೆ.' },
      oneMoment: { label: 'ಒಂದು ಕ್ಷಣ', audio: 'ದಯವಿಟ್ಟು ಒಂದು ಕ್ಷಣ ಕಾಯಿರಿ.' },
      understood: { label: 'ನಾವು ಏನು ಅರ್ಥಮಾಡಿಕೊಂಡೆವು', audio: '' },
      moreFields: { label: '+{n} ಇನ್ನಷ್ಟು', audio: '' },
      notSure: { label: 'ಖಚಿತವಿಲ್ಲ — ದಯವಿಟ್ಟು ಪರಿಶೀಲಿಸಿ', audio: '' },
      edit: { label: 'ಬದಲಾಯಿಸಿ', audio: 'ಈ ಉತ್ತರವನ್ನು ಬದಲಾಯಿಸಿ.' },
      micUnavailable: {
        label: 'ನೀವು ಉತ್ತರವನ್ನು ಒತ್ತಿ ಆಯ್ಕೆ ಮಾಡಬಹುದು',
        audio: 'ಮೈಕ್ ಕೆಲಸ ಮಾಡುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ಉತ್ತರವನ್ನು ಒತ್ತಿ ಆಯ್ಕೆ ಮಾಡಿ.',
      },
    },
    idle: {
      begin: { label: 'ಪ್ರಾರಂಭಿಸಲು ಇಲ್ಲಿ ಸ್ಪರ್ಶಿಸಿ', audio: 'ಪ್ರಾರಂಭಿಸಲು ಪರದೆಯನ್ನು ಸ್ಪರ್ಶಿಸಿ.' },
      subtitle: { label: 'ಆಯುಷ್ ಸಚಿವಾಲಯ · ಹೊರರೋಗಿ ವಿಭಾಗ', audio: '' },
    },
    language: {
      title: { label: 'ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆರಿಸಿ', audio: 'ದಯವಿಟ್ಟು ನಿಮ್ಮ ಭಾಷೆಯನ್ನು ಆರಿಸಿ.' },
      greeting: { label: 'ಕನ್ನಡ', audio: 'ನಮಸ್ಕಾರ. ಕನ್ನಡ ಆಯ್ಕೆಯಾಗಿದೆ. ಪ್ರಾರಂಭಿಸೋಣ.' },
    },
    identify: {
      title: { label: 'ನಿಮ್ಮ ದಾಖಲೆಯನ್ನು ಹುಡುಕೋಣ', audio: 'ನಿಮ್ಮ ದಾಖಲೆಯನ್ನು ಹುಡುಕೋಣ. ದಯವಿಟ್ಟು ಒಂದನ್ನು ಆರಿಸಿ.' },
      abha: { label: 'ನನ್ನ ಬಳಿ ಆಭಾ ಸಂಖ್ಯೆ ಇದೆ', audio: 'ನನ್ನ ಬಳಿ ಆಭಾ ಸಂಖ್ಯೆ ಇದೆ.' },
      aadhaar: { label: 'ನನ್ನ ಬಳಿ ಆಧಾರ್ ಇದೆ', audio: 'ನನ್ನ ಬಳಿ ಆಧಾರ್ ಸಂಖ್ಯೆ ಇದೆ.' },
      newHere: { label: 'ನಾನು ಇಲ್ಲಿ ಹೊಸಬ', audio: 'ನಾನು ಇಲ್ಲಿ ಹೊಸಬ.' },
      abhaTitle: { label: 'ನಿಮ್ಮ ಆಭಾ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ', audio: 'ದಯವಿಟ್ಟು ಅಂಕೆಗಳಿಂದ ನಿಮ್ಮ ಆಭಾ ಸಂಖ್ಯೆ ಬರೆಯಿರಿ.' },
      aadhaarTitle: { label: 'ನಿಮ್ಮ ಆಧಾರ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ', audio: 'ದಯವಿಟ್ಟು ಅಂಕೆಗಳಿಂದ ನಿಮ್ಮ ಆಧಾರ್ ಸಂಖ್ಯೆ ಬರೆಯಿರಿ.' },
      checking: { label: 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ', audio: 'ನಿಮ್ಮ ಸಂಖ್ಯೆ ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ. ಒಂದು ಕ್ಷಣ.' },
      nameTitle: { label: 'ನಿಮ್ಮ ಹೆಸರೇನು?', audio: 'ನಿಮ್ಮ ಹೆಸರೇನು? ನೀವು ಹೇಳಬಹುದು ಅಥವಾ ಬರೆಯಬಹುದು.' },
      ageTitle: { label: 'ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು?', audio: 'ನಿಮ್ಮ ವಯಸ್ಸು ಎಷ್ಟು? ದಯವಿಟ್ಟು ಅಂಕೆಗಳಿಂದ ಬರೆಯಿರಿ.' },
      sexTitle: { label: 'ದಯವಿಟ್ಟು ಆರಿಸಿ', audio: 'ದಯವಿಟ್ಟು ಒಂದನ್ನು ಆರಿಸಿ.' },
      male: { label: 'ಪುರುಷ', audio: 'ಪುರುಷ.' },
      female: { label: 'ಮಹಿಳೆ', audio: 'ಮಹಿಳೆ.' },
      otherSex: { label: 'ಇತರೆ', audio: 'ಇತರೆ.' },
    },
    consent: {
      title: { label: 'ನಿಮ್ಮ ಅನುಮತಿ', audio: '' },
      explanation: {
        label:
          'ಈ ಯಂತ್ರವು ನಿಮ್ಮ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತದೆ ಮತ್ತು ನಿಮ್ಮ ಉತ್ತರಗಳನ್ನು ನಿಮ್ಮ ಧ್ವನಿಯಲ್ಲಿ ದಾಖಲಿಸುತ್ತದೆ. ನಿಮ್ಮ ಹಳೆಯ ಚೀಟಿ ಮತ್ತು ವರದಿಗಳ ಚಿತ್ರಗಳನ್ನೂ ಓದಬಹುದು. ಈ ಮಾಹಿತಿಯನ್ನು ಇಂದು ನಿಮ್ಮನ್ನು ನೋಡುವ ವೈದ್ಯರು ಮಾತ್ರ ಓದುತ್ತಾರೆ. ಬೇರೆ ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳುವುದಿಲ್ಲ. ನೀವು ನಿರಾಕರಿಸಬಹುದು. ನಿರಾಕರಿಸಿದರೂ ನೀವು ಎಂದಿನಂತೆ ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗಬಹುದು.',
        audio:
          'ದಯವಿಟ್ಟು ಗಮನವಿಟ್ಟು ಕೇಳಿ. ಈ ಯಂತ್ರವು ನಿಮ್ಮ ಆರೋಗ್ಯದ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳುತ್ತದೆ ಮತ್ತು ನಿಮ್ಮ ಉತ್ತರಗಳನ್ನು ನಿಮ್ಮ ಧ್ವನಿಯಲ್ಲಿ ದಾಖಲಿಸುತ್ತದೆ. ನಿಮ್ಮ ಹಳೆಯ ಚೀಟಿ ಮತ್ತು ವರದಿಗಳ ಚಿತ್ರಗಳನ್ನೂ ಓದಬಹುದು. ಈ ಮಾಹಿತಿಯನ್ನು ಇಂದು ನಿಮ್ಮನ್ನು ನೋಡುವ ವೈದ್ಯರು ಮಾತ್ರ ಓದುತ್ತಾರೆ. ಬೇರೆ ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳುವುದಿಲ್ಲ. ನೀವು ನಿರಾಕರಿಸಬಹುದು. ನಿರಾಕರಿಸಿದರೂ ನೀವು ಎಂದಿನಂತೆ ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗಬಹುದು.',
      },
      playAgain: { label: 'ಮತ್ತೆ ಕೇಳಿ', audio: '' },
      optHistory: { label: 'ನನ್ನ ಆರೋಗ್ಯ ವಿವರವನ್ನು ದಾಖಲಿಸಿ', audio: 'ನನ್ನ ಆರೋಗ್ಯ ವಿವರವನ್ನು ದಾಖಲಿಸಿ.' },
      optDocuments: { label: 'ನನ್ನ ಹಳೆಯ ದಾಖಲೆಗಳನ್ನು ಓದಿ', audio: 'ನನ್ನ ಹಳೆಯ ದಾಖಲೆಗಳನ್ನು ಓದಿ.' },
      optAbha: { label: 'ಇದನ್ನು ನನ್ನ ಆಭಾ ದಾಖಲೆಗೆ ಜೋಡಿಸಿ', audio: 'ಇದನ್ನು ನನ್ನ ಆಭಾ ದಾಖಲೆಗೆ ಜೋಡಿಸಿ.' },
      agree: { label: 'ನಾನು ಒಪ್ಪುತ್ತೇನೆ', audio: 'ನಾನು ಒಪ್ಪುತ್ತೇನೆ.' },
      decline: { label: 'ನಾನು ಒಪ್ಪುವುದಿಲ್ಲ', audio: 'ನಾನು ಒಪ್ಪುವುದಿಲ್ಲ.' },
      declinedTitle: { label: 'ಪರವಾಗಿಲ್ಲ', audio: 'ಪರವಾಗಿಲ್ಲ.' },
      declinedBody: {
        label: 'ನೀವು ಎಂದಿನಂತೆ ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗಬಹುದು. ದಯವಿಟ್ಟು ಕೌಂಟರ್‌ಗೆ ಹೋಗಿ.',
        audio: 'ನೀವು ಎಂದಿನಂತೆ ವೈದ್ಯರನ್ನು ಭೇಟಿಯಾಗಬಹುದು. ದಯವಿಟ್ಟು ಕೌಂಟರ್‌ಗೆ ಹೋಗಿ.',
      },
    },
    complaint: {
      title: { label: 'ಇಂದು ನಿಮಗೆ ಏನು ತೊಂದರೆ?', audio: 'ಇಂದು ನಿಮಗೆ ಏನು ತೊಂದರೆ? ನೀವು ಮಾತನಾಡಬಹುದು ಅಥವಾ ಚಿತ್ರವನ್ನು ಒತ್ತಬಹುದು.' },
      head: { label: 'ತಲೆ', audio: 'ತಲೆ.' },
      chest: { label: 'ಎದೆ', audio: 'ಎದೆ.' },
      stomach: { label: 'ಹೊಟ್ಟೆ', audio: 'ಹೊಟ್ಟೆ.' },
      back: { label: 'ಬೆನ್ನು', audio: 'ಬೆನ್ನು.' },
      joints: { label: 'ಕೀಲುಗಳು', audio: 'ಕೀಲುಗಳು.' },
      skin: { label: 'ಚರ್ಮ', audio: 'ಚರ್ಮ.' },
      fever: { label: 'ಜ್ವರ', audio: 'ಜ್ವರ.' },
      breathing: { label: 'ಉಸಿರಾಟ', audio: 'ಉಸಿರಾಟ.' },
      other: { label: 'ಬೇರೇನೋ', audio: 'ಬೇರೇನೋ.' },
    },
    documents: {
      title: { label: 'ನಿಮ್ಮ ಬಳಿ ಹಳೆಯ ಚೀಟಿ ಅಥವಾ ವರದಿ ಇದೆಯೇ?', audio: 'ಇಂದು ನಿಮ್ಮ ಬಳಿ ಹಳೆಯ ಚೀಟಿ ಅಥವಾ ವರದಿ ಇದೆಯೇ?' },
      yes: { label: 'ಹೌದು, ನನ್ನ ಬಳಿ ಕಾಗದಗಳಿವೆ', audio: 'ಹೌದು, ನನ್ನ ಬಳಿ ಕಾಗದಗಳಿವೆ.' },
      no: { label: 'ಇಲ್ಲ, ಮುಂದೆ ಹೋಗಿ', audio: 'ಇಲ್ಲ, ಮುಂದೆ ಹೋಗಿ.' },
      cameraTitle: { label: 'ಕಾಗದವನ್ನು ಚೌಕಟ್ಟಿನ ಒಳಗೆ ಹಿಡಿಯಿರಿ', audio: 'ಕಾಗದವನ್ನು ಸಮತಟ್ಟಾಗಿ ಚೌಕಟ್ಟಿನ ಒಳಗೆ ಹಿಡಿದು, ದುಂಡಗಿನ ಗುಂಡಿಯನ್ನು ಒತ್ತಿ.' },
      capture: { label: 'ಫೋಟೋ ತೆಗೆಯಿರಿ', audio: 'ಫೋಟೋ ತೆಗೆಯಿರಿ.' },
      addAnother: { label: 'ಇನ್ನೊಂದು ಸೇರಿಸಿ', audio: 'ಇನ್ನೊಂದು ಕಾಗದ ಸೇರಿಸಿ.' },
      done: { label: 'ಮುಗಿಯಿತು', audio: 'ಮುಗಿಯಿತು.' },
      remove: { label: 'ತೆಗೆದುಹಾಕಿ', audio: 'ತೆಗೆದುಹಾಕಲಾಗಿದೆ.' },
      cameraBlocked: {
        label: 'ಕ್ಯಾಮೆರಾ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಕಾಗದಗಳನ್ನು ವೈದ್ಯರಿಗೆ ತೋರಿಸಿ.',
        audio: 'ಕ್ಯಾಮೆರಾ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಕಾಗದಗಳನ್ನು ವೈದ್ಯರಿಗೆ ತೋರಿಸಿ.',
      },
    },
    confirm: {
      title: { label: 'ನೀವು ಹೇಳಿದ್ದನ್ನು ಪರಿಶೀಲಿಸಿ', audio: 'ದಯವಿಟ್ಟು ಕೇಳಿ ಮತ್ತು ನೀವು ಹೇಳಿದ್ದನ್ನು ಪರಿಶೀಲಿಸಿ.' },
      correct: { label: 'ಹೌದು, ಇದು ಸರಿ', audio: 'ಹೌದು, ಇದು ಸರಿ.' },
      nothing: { label: 'ಏನೂ ದಾಖಲಾಗಿಲ್ಲ', audio: 'ಏನೂ ದಾಖಲಾಗಿಲ್ಲ.' },
    },
    done: {
      title: { label: 'ಧನ್ಯವಾದ', audio: 'ಧನ್ಯವಾದ.' },
      token: { label: 'ನಿಮ್ಮ ಟೋಕನ್ ಸಂಖ್ಯೆ', audio: '' },
      room: { label: 'ವೈದ್ಯರ ಕೊಠಡಿ', audio: '' },
      wait: { label: 'ದಯವಿಟ್ಟು ಕಾಯಿರಿ. ನಿಮ್ಮನ್ನು ಕರೆಯಲಾಗುವುದು.', audio: 'ದಯವಿಟ್ಟು ಕಾಯಿರಿ. ನಿಮ್ಮನ್ನು ಕರೆಯಲಾಗುವುದು.' },
    },
    emergency: {
      patient: { label: 'ದಯವಿಟ್ಟು ಈಗಲೇ ತುರ್ತು ಕೌಂಟರ್‌ಗೆ ಹೋಗಿ', audio: 'ದಯವಿಟ್ಟು ಈಗಲೇ ತುರ್ತು ಕೌಂಟರ್‌ಗೆ ಹೋಗಿ. ಈ ಪರದೆಯನ್ನು ಸಿಬ್ಬಂದಿಗೆ ತೋರಿಸಿ.' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'ನೀವು ಇನ್ನೂ ಇದ್ದೀರಾ?', audio: 'ನೀವು ಇನ್ನೂ ಇದ್ದೀರಾ?' },
      continue: { label: 'ಹೌದು, ಮುಂದುವರಿಸಿ', audio: 'ಹೌದು, ಮುಂದುವರಿಸಿ.' },
      closing: { label: 'ಮುಚ್ಚಲಾಗುತ್ತಿದೆ', audio: '' },
    },
    error: {
      title: { label: 'ಏನೋ ತಪ್ಪಾಗಿದೆ', audio: 'ಏನೋ ತಪ್ಪಾಗಿದೆ. ದಯವಿಟ್ಟು ಸಿಬ್ಬಂದಿಯನ್ನು ಕರೆಯಿರಿ.' },
      body: { label: 'ದಯವಿಟ್ಟು ಸಿಬ್ಬಂದಿಯನ್ನು ಕರೆಯಿರಿ.', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'ಮತ್ತೆ ಪ್ರಾರಂಭಿಸಿ', audio: '' },
    },
  },

  ta: {
    phase: {
      identity: { label: 'சில அடிப்படை விவரங்களுடன் தொடங்குவோம்.', audio: '' },
      consent: { label: 'தொடங்கும் முன் உங்கள் சம்மதம் தேவை.', audio: '' },
      chief_complaint: { label: 'இன்று உங்களுக்கு என்ன பிரச்சினை?', audio: '' },
      hpi: { label: 'இந்தப் பிரச்சினை பற்றி மேலும் சொல்லுங்கள்.', audio: '' },
      ros: { label: 'உங்கள் ஒட்டுமொத்த உடல்நிலை பற்றி ஒரு சிறிய கேள்வி.', audio: '' },
      past_medical: { label: 'உங்களுக்கு நீடித்த நோய் அல்லது முன்பு அறுவை சிகிச்சை உண்டா?', audio: '' },
      drug_allergy: { label: 'நீங்கள் ஏதேனும் மருந்து எடுக்கிறீர்களா, ஒவ்வாமை உண்டா?', audio: '' },
      family: { label: 'உங்கள் குடும்பத்தில் யாருக்கேனும் கடுமையான நோய் உண்டா?', audio: '' },
      personal: { label: 'வாழ்க்கை முறை பற்றிய சில கேள்விகள்.', audio: '' },
      documents: { label: 'உங்களிடம் பழைய சீட்டு அல்லது பரிசோதனை அறிக்கை உள்ளதா?', audio: '' },
      confirm: { label: 'முடிக்கும் முன் உங்கள் பதில்களைப் பாருங்கள்.', audio: '' },
    },
    common: {
      repeat: { label: 'மீண்டும் கேட்க', audio: 'இதை மீண்டும் கேளுங்கள்.' },
      listen: { label: 'கேளுங்கள்', audio: '' },
      stop: { label: 'நிறுத்து', audio: '' },
      back: { label: 'பின்', audio: 'பின்னால் செல்கிறோம்.' },
      next: { label: 'அடுத்து', audio: 'அடுத்த கேள்வி.' },
      yes: { label: 'ஆம்', audio: 'ஆம்.' },
      no: { label: 'இல்லை', audio: 'இல்லை.' },
      doneSpeaking: { label: 'பேசி முடித்தேன்', audio: 'பேசி முடித்தேன்.' },
      tapToSpeak: { label: 'பேச தொடவும்', audio: 'பச்சை வட்டத்தைத் தொட்டு பேசுங்கள்.' },
      tapOrType: {
        label: 'பேச மைக்கை அழுத்துங்கள், அல்லது இங்கே எழுதுங்கள்',
        audio: 'பச்சை வட்டத்தை அழுத்திப் பேசுங்கள், அல்லது உங்கள் பதிலை இங்கே எழுதுங்கள்.',
      },
      typeHere: {
        label: 'உங்கள் பதிலை இங்கே எழுதுங்கள்',
        audio: 'மைக் வேலை செய்யவில்லை. உங்கள் பதிலை இங்கே எழுதுங்கள்.',
      },
      listening: { label: 'கேட்கிறது', audio: 'நான் கேட்கிறேன்.' },
      oneMoment: { label: 'ஒரு நிமிடம்', audio: 'தயவுசெய்து ஒரு நிமிடம் காத்திருங்கள்.' },
      understood: { label: 'நாங்கள் புரிந்துகொண்டது', audio: '' },
      moreFields: { label: '+{n} மேலும்', audio: '' },
      notSure: { label: 'உறுதியாக இல்லை — சரிபார்க்கவும்', audio: '' },
      edit: { label: 'மாற்று', audio: 'இந்த பதிலை மாற்றுங்கள்.' },
      micUnavailable: {
        label: 'உங்கள் பதிலைத் தொட்டும் தேர்வு செய்யலாம்',
        audio: 'ஒலிவாங்கி வேலை செய்யவில்லை. தயவுசெய்து உங்கள் பதிலைத் தொட்டு தேர்வு செய்யுங்கள்.',
      },
    },
    idle: {
      begin: { label: 'தொடங்க இங்கே தொடவும்', audio: 'தொடங்க திரையைத் தொடுங்கள்.' },
      subtitle: { label: 'ஆயுஷ் அமைச்சகம் · வெளிநோயாளர் பிரிவு', audio: '' },
    },
    language: {
      title: { label: 'உங்கள் மொழியைத் தேர்ந்தெடுங்கள்', audio: 'தயவுசெய்து உங்கள் மொழியைத் தேர்ந்தெடுங்கள்.' },
      greeting: { label: 'தமிழ்', audio: 'வணக்கம். தமிழ் தேர்ந்தெடுக்கப்பட்டது. தொடங்குவோம்.' },
    },
    identify: {
      title: { label: 'உங்கள் பதிவைத் தேடுவோம்', audio: 'உங்கள் பதிவைத் தேடுவோம். தயவுசெய்து ஒன்றைத் தேர்ந்தெடுங்கள்.' },
      abha: { label: 'என்னிடம் ஆபா எண் உள்ளது', audio: 'என்னிடம் ஆபா எண் உள்ளது.' },
      aadhaar: { label: 'என்னிடம் ஆதார் உள்ளது', audio: 'என்னிடம் ஆதார் எண் உள்ளது.' },
      newHere: { label: 'நான் இங்கு புதியவர்', audio: 'நான் இங்கு புதியவர்.' },
      abhaTitle: { label: 'உங்கள் ஆபா எண்ணை உள்ளிடவும்', audio: 'தயவுசெய்து எண்களைக் கொண்டு உங்கள் ஆபா எண்ணை உள்ளிடுங்கள்.' },
      aadhaarTitle: { label: 'உங்கள் ஆதார் எண்ணை உள்ளிடவும்', audio: 'தயவுசெய்து எண்களைக் கொண்டு உங்கள் ஆதார் எண்ணை உள்ளிடுங்கள்.' },
      checking: { label: 'சரிபார்க்கிறது', audio: 'உங்கள் எண் சரிபார்க்கப்படுகிறது. ஒரு நிமிடம்.' },
      nameTitle: { label: 'உங்கள் பெயர் என்ன?', audio: 'உங்கள் பெயர் என்ன? நீங்கள் சொல்லலாம் அல்லது தட்டச்சு செய்யலாம்.' },
      ageTitle: { label: 'உங்கள் வயது என்ன?', audio: 'உங்கள் வயது என்ன? தயவுசெய்து எண்களைக் கொண்டு உள்ளிடுங்கள்.' },
      sexTitle: { label: 'தயவுசெய்து தேர்ந்தெடுக்கவும்', audio: 'தயவுசெய்து ஒன்றைத் தேர்ந்தெடுங்கள்.' },
      male: { label: 'ஆண்', audio: 'ஆண்.' },
      female: { label: 'பெண்', audio: 'பெண்.' },
      otherSex: { label: 'மற்றவை', audio: 'மற்றவை.' },
    },
    consent: {
      title: { label: 'உங்கள் அனுமதி', audio: '' },
      explanation: {
        label:
          'இந்த இயந்திரம் உங்கள் உடல்நலம் குறித்து கேள்விகள் கேட்டு, உங்கள் பதில்களை உங்கள் குரலில் பதிவு செய்யும். உங்கள் பழைய மருந்துச் சீட்டுகள் மற்றும் அறிக்கைகளின் புகைப்படங்களையும் படிக்கலாம். இந்தத் தகவலை இன்று உங்களைப் பார்க்கும் மருத்துவர் மட்டுமே பார்ப்பார். வேறு யாருடனும் பகிரப்படாது. நீங்கள் மறுக்கலாம். மறுத்தாலும் வழக்கம் போல் மருத்துவரை சந்திக்கலாம்.',
        audio:
          'தயவுசெய்து கவனமாகக் கேளுங்கள். இந்த இயந்திரம் உங்கள் உடல்நலம் குறித்து கேள்விகள் கேட்டு, உங்கள் பதில்களை உங்கள் குரலில் பதிவு செய்யும். உங்கள் பழைய மருந்துச் சீட்டுகள் மற்றும் அறிக்கைகளின் புகைப்படங்களையும் படிக்கலாம். இந்தத் தகவலை இன்று உங்களைப் பார்க்கும் மருத்துவர் மட்டுமே பார்ப்பார். வேறு யாருடனும் பகிரப்படாது. நீங்கள் மறுக்கலாம். மறுத்தாலும் வழக்கம் போல் மருத்துவரை சந்திக்கலாம்.',
      },
      playAgain: { label: 'மீண்டும் கேட்க', audio: '' },
      optHistory: { label: 'என் மருத்துவ விவரத்தைப் பதிவு செய்யுங்கள்', audio: 'என் மருத்துவ விவரத்தைப் பதிவு செய்யுங்கள்.' },
      optDocuments: { label: 'என் பழைய ஆவணங்களைப் படியுங்கள்', audio: 'என் பழைய ஆவணங்களைப் படியுங்கள்.' },
      optAbha: { label: 'இதை என் ஆபா பதிவுடன் இணையுங்கள்', audio: 'இதை என் ஆபா பதிவுடன் இணையுங்கள்.' },
      agree: { label: 'நான் ஒப்புக்கொள்கிறேன்', audio: 'நான் ஒப்புக்கொள்கிறேன்.' },
      decline: { label: 'நான் ஒப்புக்கொள்ளவில்லை', audio: 'நான் ஒப்புக்கொள்ளவில்லை.' },
      declinedTitle: { label: 'பரவாயில்லை', audio: 'பரவாயில்லை.' },
      declinedBody: {
        label: 'வழக்கம் போல் மருத்துவரை சந்திக்கலாம். தயவுசெய்து கவுண்டருக்குச் செல்லுங்கள்.',
        audio: 'வழக்கம் போல் மருத்துவரை சந்திக்கலாம். தயவுசெய்து கவுண்டருக்குச் செல்லுங்கள்.',
      },
    },
    complaint: {
      title: { label: 'இன்று உங்களுக்கு என்ன பிரச்சனை?', audio: 'இன்று உங்களுக்கு என்ன பிரச்சனை? நீங்கள் பேசலாம், அல்லது படத்தைத் தொடலாம்.' },
      head: { label: 'தலை', audio: 'தலை.' },
      chest: { label: 'மார்பு', audio: 'மார்பு.' },
      stomach: { label: 'வயிறு', audio: 'வயிறு.' },
      back: { label: 'முதுகு', audio: 'முதுகு.' },
      joints: { label: 'மூட்டுகள்', audio: 'மூட்டுகள்.' },
      skin: { label: 'தோல்', audio: 'தோல்.' },
      fever: { label: 'காய்ச்சல்', audio: 'காய்ச்சல்.' },
      breathing: { label: 'மூச்சு', audio: 'மூச்சு.' },
      other: { label: 'வேறு ஏதோ', audio: 'வேறு ஏதோ.' },
    },
    documents: {
      title: { label: 'உங்களிடம் பழைய மருந்துச் சீட்டு அல்லது அறிக்கை உள்ளதா?', audio: 'இன்று உங்களிடம் பழைய மருந்துச் சீட்டு அல்லது அறிக்கை உள்ளதா?' },
      yes: { label: 'ஆம், என்னிடம் காகிதங்கள் உள்ளன', audio: 'ஆம், என்னிடம் காகிதங்கள் உள்ளன.' },
      no: { label: 'இல்லை, தவிர்க்கவும்', audio: 'இல்லை, தவிர்க்கவும்.' },
      cameraTitle: { label: 'காகிதத்தை பெட்டிக்குள் வைக்கவும்', audio: 'காகிதத்தை நேராக பெட்டிக்குள் வைத்து, வட்ட பொத்தானை அழுத்துங்கள்.' },
      capture: { label: 'புகைப்படம் எடு', audio: 'புகைப்படம் எடு.' },
      addAnother: { label: 'மற்றொன்று சேர்', audio: 'மற்றொரு காகிதம் சேர்.' },
      done: { label: 'முடிந்தது', audio: 'முடிந்தது.' },
      remove: { label: 'நீக்கு', audio: 'நீக்கப்பட்டது.' },
      cameraBlocked: {
        label: 'கேமரா கிடைக்கவில்லை. உங்கள் காகிதங்களை மருத்துவரிடம் காட்டுங்கள்.',
        audio: 'கேமரா கிடைக்கவில்லை. உங்கள் காகிதங்களை மருத்துவரிடம் காட்டுங்கள்.',
      },
    },
    confirm: {
      title: { label: 'நீங்கள் சொன்னதைச் சரிபார்க்கவும்', audio: 'தயவுசெய்து கேட்டு, நீங்கள் சொன்னதைச் சரிபாருங்கள்.' },
      correct: { label: 'ஆம், இது சரி', audio: 'ஆம், இது சரி.' },
      nothing: { label: 'எதுவும் பதிவாகவில்லை', audio: 'எதுவும் பதிவாகவில்லை.' },
    },
    done: {
      title: { label: 'நன்றி', audio: 'நன்றி.' },
      token: { label: 'உங்கள் டோக்கன் எண்', audio: '' },
      room: { label: 'மருத்துவர் அறை', audio: '' },
      wait: { label: 'தயவுசெய்து காத்திருங்கள். உங்களை அழைப்பார்கள்.', audio: 'தயவுசெய்து காத்திருங்கள். உங்களை அழைப்பார்கள்.' },
    },
    emergency: {
      patient: { label: 'தயவுசெய்து இப்போதே அவசர கவுண்டருக்குச் செல்லுங்கள்', audio: 'தயவுசெய்து இப்போதே அவசர கவுண்டருக்குச் செல்லுங்கள். இந்தத் திரையை ஊழியரிடம் காட்டுங்கள்.' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'நீங்கள் இன்னும் இருக்கிறீர்களா?', audio: 'நீங்கள் இன்னும் இருக்கிறீர்களா?' },
      continue: { label: 'ஆம், தொடரவும்', audio: 'ஆம், தொடரவும்.' },
      closing: { label: 'மூடப்படுகிறது', audio: '' },
    },
    error: {
      title: { label: 'ஏதோ தவறு நடந்துவிட்டது', audio: 'ஏதோ தவறு நடந்தது. தயவுசெய்து ஊழியரை அழைக்கவும்.' },
      body: { label: 'தயவுசெய்து ஊழியரை அழைக்கவும்.', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'மீண்டும் தொடங்கு', audio: '' },
    },
  },

  te: {
    phase: {
      identity: { label: 'కొన్ని ప్రాథమిక వివరాలతో మొదలుపెడదాం.', audio: '' },
      consent: { label: 'మొదలుపెట్టే ముందు మీ సమ్మతి కావాలి.', audio: '' },
      chief_complaint: { label: 'ఈ రోజు మీకు ఏమి ఇబ్బంది?', audio: '' },
      hpi: { label: 'ఈ సమస్య గురించి ఇంకా చెప్పండి.', audio: '' },
      ros: { label: 'మీ మొత్తం ఆరోగ్యం గురించి ఒక చిన్న ప్రశ్న.', audio: '' },
      past_medical: { label: 'మీకు దీర్ఘకాలిక వ్యాధి లేదా గతంలో ఆపరేషన్ ఉందా?', audio: '' },
      drug_allergy: { label: 'మీరు ఏదైనా మందు వాడుతున్నారా, అలర్జీ ఉందా?', audio: '' },
      family: { label: 'మీ కుటుంబంలో ఎవరికైనా తీవ్రమైన వ్యాధి ఉందా?', audio: '' },
      personal: { label: 'జీవనశైలికి సంబంధించిన కొన్ని ప్రశ్నలు.', audio: '' },
      documents: { label: 'మీ దగ్గర పాత చీటీలు లేదా పరీక్ష నివేదికలు ఉన్నాయా?', audio: '' },
      confirm: { label: 'ముగించే ముందు మీ సమాధానాలు చూసుకోండి.', audio: '' },
    },
    common: {
      repeat: { label: 'మళ్లీ వినండి', audio: 'దీన్ని మళ్లీ వినండి.' },
      listen: { label: 'వినండి', audio: '' },
      stop: { label: 'ఆపండి', audio: '' },
      back: { label: 'వెనుకకు', audio: 'వెనుకకు వెళ్తున్నాము.' },
      next: { label: 'తరువాత', audio: 'తదుపరి ప్రశ్న.' },
      yes: { label: 'అవును', audio: 'అవును.' },
      no: { label: 'కాదు', audio: 'కాదు.' },
      doneSpeaking: { label: 'మాట్లాడటం పూర్తయింది', audio: 'మాట్లాడటం పూర్తయింది.' },
      tapToSpeak: { label: 'మాట్లాడటానికి నొక్కండి', audio: 'ఆకుపచ్చ వృత్తాన్ని నొక్కి మాట్లాడండి.' },
      tapOrType: {
        label: 'మాట్లాడటానికి మైక్ నొక్కండి, లేదా ఇక్కడ రాయండి',
        audio: 'ఆకుపచ్చ వృత్తాన్ని నొక్కి మాట్లాడండి, లేదా మీ సమాధానాన్ని ఇక్కడ రాయండి.',
      },
      typeHere: {
        label: 'మీ సమాధానాన్ని ఇక్కడ రాయండి',
        audio: 'మైక్ పని చేయడం లేదు. దయచేసి మీ సమాధానాన్ని ఇక్కడ రాయండి.',
      },
      listening: { label: 'వింటున్నాము', audio: 'నేను వింటున్నాను.' },
      oneMoment: { label: 'ఒక్క క్షణం', audio: 'దయచేసి ఒక్క క్షణం ఆగండి.' },
      understood: { label: 'మేము అర్థం చేసుకున్నది', audio: '' },
      moreFields: { label: '+{n} మరిన్ని', audio: '' },
      notSure: { label: 'ఖచ్చితంగా తెలియదు — తనిఖీ చేయండి', audio: '' },
      edit: { label: 'మార్చు', audio: 'ఈ సమాధానాన్ని మార్చండి.' },
      micUnavailable: {
        label: 'మీరు సమాధానాన్ని నొక్కి కూడా ఎంచుకోవచ్చు',
        audio: 'మైక్ పని చేయడం లేదు. దయచేసి మీ సమాధానాన్ని నొక్కి ఎంచుకోండి.',
      },
    },
    idle: {
      begin: { label: 'ప్రారంభించడానికి ఇక్కడ తాకండి', audio: 'ప్రారంభించడానికి తెరను తాకండి.' },
      subtitle: { label: 'ఆయుష్ మంత్రిత్వ శాఖ · ఔట్ పేషెంట్ విభాగం', audio: '' },
    },
    language: {
      title: { label: 'మీ భాషను ఎంచుకోండి', audio: 'దయచేసి మీ భాషను ఎంచుకోండి.' },
      greeting: { label: 'తెలుగు', audio: 'నమస్కారం. తెలుగు ఎంపిక చేయబడింది. ప్రారంభిద్దాం.' },
    },
    identify: {
      title: { label: 'మీ రికార్డును వెతుకుదాం', audio: 'మీ రికార్డును వెతుకుదాం. దయచేసి ఒకటి ఎంచుకోండి.' },
      abha: { label: 'నా దగ్గర ఆభా నంబర్ ఉంది', audio: 'నా దగ్గర ఆభా నంబర్ ఉంది.' },
      aadhaar: { label: 'నా దగ్గర ఆధార్ ఉంది', audio: 'నా దగ్గర ఆధార్ నంబర్ ఉంది.' },
      newHere: { label: 'నేను ఇక్కడ కొత్త', audio: 'నేను ఇక్కడ కొత్త.' },
      abhaTitle: { label: 'మీ ఆభా నంబర్ నమోదు చేయండి', audio: 'దయచేసి అంకెలతో మీ ఆభా నంబర్ నమోదు చేయండి.' },
      aadhaarTitle: { label: 'మీ ఆధార్ నంబర్ నమోదు చేయండి', audio: 'దయచేసి అంకెలతో మీ ఆధార్ నంబర్ నమోదు చేయండి.' },
      checking: { label: 'తనిఖీ చేస్తోంది', audio: 'మీ నంబర్ తనిఖీ చేయబడుతోంది. ఒక్క క్షణం.' },
      nameTitle: { label: 'మీ పేరు ఏమిటి?', audio: 'మీ పేరు ఏమిటి? మీరు చెప్పవచ్చు లేదా టైప్ చేయవచ్చు.' },
      ageTitle: { label: 'మీ వయస్సు ఎంత?', audio: 'మీ వయస్సు ఎంత? దయచేసి అంకెలతో నమోదు చేయండి.' },
      sexTitle: { label: 'దయచేసి ఎంచుకోండి', audio: 'దయచేసి ఒకటి ఎంచుకోండి.' },
      male: { label: 'పురుషుడు', audio: 'పురుషుడు.' },
      female: { label: 'స్త్రీ', audio: 'స్త్రీ.' },
      otherSex: { label: 'ఇతర', audio: 'ఇతర.' },
    },
    consent: {
      title: { label: 'మీ అనుమతి', audio: '' },
      explanation: {
        label:
          'ఈ యంత్రం మీ ఆరోగ్యం గురించి ప్రశ్నలు అడిగి, మీ సమాధానాలను మీ స్వరంలో నమోదు చేస్తుంది. మీ పాత చీటీలు మరియు నివేదికల ఫోటోలను కూడా చదవగలదు. ఈ సమాచారాన్ని ఈ రోజు మిమ్మల్ని చూసే వైద్యుడు మాత్రమే చూస్తారు. ఇతరులతో ఏదీ పంచుకోబడదు. మీరు నిరాకరించవచ్చు. నిరాకరించినా మీరు మామూలుగా వైద్యుడిని కలవవచ్చు.',
        audio:
          'దయచేసి శ్రద్ధగా వినండి. ఈ యంత్రం మీ ఆరోగ్యం గురించి ప్రశ్నలు అడిగి, మీ సమాధానాలను మీ స్వరంలో నమోదు చేస్తుంది. మీ పాత చీటీలు మరియు నివేదికల ఫోటోలను కూడా చదవగలదు. ఈ సమాచారాన్ని ఈ రోజు మిమ్మల్ని చూసే వైద్యుడు మాత్రమే చూస్తారు. ఇతరులతో ఏదీ పంచుకోబడదు. మీరు నిరాకరించవచ్చు. నిరాకరించినా మీరు మామూలుగా వైద్యుడిని కలవవచ్చు.',
      },
      playAgain: { label: 'మళ్లీ వినండి', audio: '' },
      optHistory: { label: 'నా ఆరోగ్య వివరాలను నమోదు చేయండి', audio: 'నా ఆరోగ్య వివరాలను నమోదు చేయండి.' },
      optDocuments: { label: 'నా పాత పత్రాలను చదవండి', audio: 'నా పాత పత్రాలను చదవండి.' },
      optAbha: { label: 'దీన్ని నా ఆభా రికార్డుకు అనుసంధానించండి', audio: 'దీన్ని నా ఆభా రికార్డుకు అనుసంధానించండి.' },
      agree: { label: 'నేను అంగీకరిస్తున్నాను', audio: 'నేను అంగీకరిస్తున్నాను.' },
      decline: { label: 'నేను అంగీకరించడం లేదు', audio: 'నేను అంగీకరించడం లేదు.' },
      declinedTitle: { label: 'ఫర్వాలేదు', audio: 'ఫర్వాలేదు.' },
      declinedBody: {
        label: 'మీరు మామూలుగా వైద్యుడిని కలవవచ్చు. దయచేసి కౌంటర్‌కు వెళ్లండి.',
        audio: 'మీరు మామూలుగా వైద్యుడిని కలవవచ్చు. దయచేసి కౌంటర్‌కు వెళ్లండి.',
      },
    },
    complaint: {
      title: { label: 'ఈ రోజు మీకు ఏమి ఇబ్బంది?', audio: 'ఈ రోజు మీకు ఏమి ఇబ్బంది? మీరు మాట్లాడవచ్చు, లేదా బొమ్మను నొక్కవచ్చు.' },
      head: { label: 'తల', audio: 'తల.' },
      chest: { label: 'ఛాతీ', audio: 'ఛాతీ.' },
      stomach: { label: 'కడుపు', audio: 'కడుపు.' },
      back: { label: 'వీపు', audio: 'వీపు.' },
      joints: { label: 'కీళ్ళు', audio: 'కీళ్ళు.' },
      skin: { label: 'చర్మం', audio: 'చర్మం.' },
      fever: { label: 'జ్వరం', audio: 'జ్వరం.' },
      breathing: { label: 'శ్వాస', audio: 'శ్వాస.' },
      other: { label: 'మరేదో', audio: 'మరేదో.' },
    },
    documents: {
      title: { label: 'మీ దగ్గర పాత చీటీ లేదా నివేదిక ఉందా?', audio: 'ఈ రోజు మీ దగ్గర పాత చీటీ లేదా నివేదిక ఉందా?' },
      yes: { label: 'అవును, నా దగ్గర కాగితాలు ఉన్నాయి', audio: 'అవును, నా దగ్గర కాగితాలు ఉన్నాయి.' },
      no: { label: 'కాదు, ముందుకు వెళ్లండి', audio: 'కాదు, ముందుకు వెళ్లండి.' },
      cameraTitle: { label: 'కాగితాన్ని పెట్టెలో ఉంచండి', audio: 'కాగితాన్ని సమంగా పెట్టెలో ఉంచి, గుండ్రని బటన్ నొక్కండి.' },
      capture: { label: 'ఫోటో తీయండి', audio: 'ఫోటో తీయండి.' },
      addAnother: { label: 'మరొకటి జోడించండి', audio: 'మరో కాగితం జోడించండి.' },
      done: { label: 'పూర్తయింది', audio: 'పూర్తయింది.' },
      remove: { label: 'తొలగించు', audio: 'తొలగించబడింది.' },
      cameraBlocked: {
        label: 'కెమెరా అందుబాటులో లేదు. దయచేసి మీ కాగితాలను వైద్యుడికి చూపించండి.',
        audio: 'కెమెరా అందుబాటులో లేదు. దయచేసి మీ కాగితాలను వైద్యుడికి చూపించండి.',
      },
    },
    confirm: {
      title: { label: 'మీరు చెప్పినది తనిఖీ చేయండి', audio: 'దయచేసి వినండి మరియు మీరు చెప్పినది తనిఖీ చేయండి.' },
      correct: { label: 'అవును, ఇది సరైనది', audio: 'అవును, ఇది సరైనది.' },
      nothing: { label: 'ఏమీ నమోదు కాలేదు', audio: 'ఏమీ నమోదు కాలేదు.' },
    },
    done: {
      title: { label: 'ధన్యవాదాలు', audio: 'ధన్యవాదాలు.' },
      token: { label: 'మీ టోకెన్ నంబర్', audio: '' },
      room: { label: 'వైద్యుని గది', audio: '' },
      wait: { label: 'దయచేసి వేచి ఉండండి. మిమ్మల్ని పిలుస్తారు.', audio: 'దయచేసి వేచి ఉండండి. మిమ్మల్ని పిలుస్తారు.' },
    },
    emergency: {
      patient: { label: 'దయచేసి వెంటనే అత్యవసర కౌంటర్‌కు వెళ్లండి', audio: 'దయచేసి వెంటనే అత్యవసర కౌంటర్‌కు వెళ్లండి. ఈ తెరను సిబ్బందికి చూపించండి.' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'మీరు ఇంకా ఉన్నారా?', audio: 'మీరు ఇంకా ఉన్నారా?' },
      continue: { label: 'అవును, కొనసాగించండి', audio: 'అవును, కొనసాగించండి.' },
      closing: { label: 'మూసివేయబడుతోంది', audio: '' },
    },
    error: {
      title: { label: 'ఏదో పొరపాటు జరిగింది', audio: 'ఏదో పొరపాటు జరిగింది. దయచేసి సిబ్బందిని పిలవండి.' },
      body: { label: 'దయచేసి సిబ్బందిని పిలవండి.', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'మళ్లీ ప్రారంభించండి', audio: '' },
    },
  },

  mr: {
    phase: {
      identity: { label: 'काही मूलभूत माहितीने सुरुवात करूया.', audio: '' },
      consent: { label: 'सुरू करण्यापूर्वी तुमची संमती हवी.', audio: '' },
      chief_complaint: { label: 'आज तुम्हाला काय त्रास होतो आहे?', audio: '' },
      hpi: { label: 'या त्रासाबद्दल आणखी सांगा.', audio: '' },
      ros: { label: 'तुमच्या एकूण तब्येतीबद्दल एक छोटा प्रश्न.', audio: '' },
      past_medical: { label: 'तुम्हाला दीर्घकालीन आजार आहे का किंवा शस्त्रक्रिया झाली आहे का?', audio: '' },
      drug_allergy: { label: 'तुम्ही कोणते औषध घेता का, आणि काही ॲलर्जी आहे का?', audio: '' },
      family: { label: 'तुमच्या कुटुंबात कोणाला गंभीर आजार आहे का?', audio: '' },
      personal: { label: 'जीवनशैलीबद्दल काही प्रश्न.', audio: '' },
      documents: { label: 'तुमच्याकडे जुनी चिठ्ठी किंवा तपासणी अहवाल आहेत का?', audio: '' },
      confirm: { label: 'संपवण्यापूर्वी तुमची उत्तरे पाहून घ्या.', audio: '' },
    },
    common: {
      repeat: { label: 'पुन्हा ऐका', audio: 'हे पुन्हा ऐका.' },
      listen: { label: 'ऐका', audio: '' },
      stop: { label: 'थांबवा', audio: '' },
      back: { label: 'मागे', audio: 'मागे जात आहोत.' },
      next: { label: 'पुढे', audio: 'पुढील प्रश्न.' },
      yes: { label: 'होय', audio: 'होय.' },
      no: { label: 'नाही', audio: 'नाही.' },
      doneSpeaking: { label: 'बोलणे पूर्ण', audio: 'बोलणे पूर्ण झाले.' },
      tapToSpeak: { label: 'बोलण्यासाठी दाबा', audio: 'हिरव्या वर्तुळावर दाबा आणि बोला.' },
      tapOrType: {
        label: 'बोलण्यासाठी माइक दाबा, किंवा येथे लिहा',
        audio: 'हिरवे वर्तुळ दाबून बोला, किंवा तुमचे उत्तर येथे लिहा.',
      },
      typeHere: {
        label: 'तुमचे उत्तर येथे लिहा',
        audio: 'माइक काम करत नाही. कृपया तुमचे उत्तर येथे लिहा.',
      },
      listening: { label: 'ऐकत आहे', audio: 'मी ऐकत आहे.' },
      oneMoment: { label: 'एक क्षण', audio: 'कृपया एक क्षण थांबा.' },
      understood: { label: 'आम्हाला काय समजले', audio: '' },
      moreFields: { label: '+{n} आणखी', audio: '' },
      notSure: { label: 'खात्री नाही — कृपया तपासा', audio: '' },
      edit: { label: 'बदला', audio: 'हे उत्तर बदला.' },
      micUnavailable: {
        label: 'तुम्ही उत्तर दाबूनही निवडू शकता',
        audio: 'माइक काम करत नाही. कृपया तुमचे उत्तर दाबून निवडा.',
      },
    },
    idle: {
      begin: { label: 'सुरू करण्यासाठी येथे स्पर्श करा', audio: 'सुरू करण्यासाठी पडद्याला स्पर्श करा.' },
      subtitle: { label: 'आयुष मंत्रालय · बाह्यरुग्ण विभाग', audio: '' },
    },
    language: {
      title: { label: 'तुमची भाषा निवडा', audio: 'कृपया तुमची भाषा निवडा.' },
      greeting: { label: 'मराठी', audio: 'नमस्कार. मराठी निवडली आहे. चला सुरू करूया.' },
    },
    identify: {
      title: { label: 'तुमची नोंद शोधूया', audio: 'तुमची नोंद शोधूया. कृपया एक निवडा.' },
      abha: { label: 'माझ्याकडे आभा क्रमांक आहे', audio: 'माझ्याकडे आभा क्रमांक आहे.' },
      aadhaar: { label: 'माझ्याकडे आधार आहे', audio: 'माझ्याकडे आधार क्रमांक आहे.' },
      newHere: { label: 'मी येथे नवीन आहे', audio: 'मी येथे नवीन आहे.' },
      abhaTitle: { label: 'तुमचा आभा क्रमांक टाका', audio: 'कृपया अंकांच्या मदतीने तुमचा आभा क्रमांक टाका.' },
      aadhaarTitle: { label: 'तुमचा आधार क्रमांक टाका', audio: 'कृपया अंकांच्या मदतीने तुमचा आधार क्रमांक टाका.' },
      checking: { label: 'तपासत आहे', audio: 'तुमचा क्रमांक तपासला जात आहे. एक क्षण.' },
      nameTitle: { label: 'तुमचे नाव काय आहे?', audio: 'तुमचे नाव काय आहे? तुम्ही बोलू शकता किंवा लिहू शकता.' },
      ageTitle: { label: 'तुमचे वय किती आहे?', audio: 'तुमचे वय किती आहे? कृपया अंकांनी लिहा.' },
      sexTitle: { label: 'कृपया निवडा', audio: 'कृपया एक निवडा.' },
      male: { label: 'पुरुष', audio: 'पुरुष.' },
      female: { label: 'महिला', audio: 'महिला.' },
      otherSex: { label: 'इतर', audio: 'इतर.' },
    },
    consent: {
      title: { label: 'तुमची परवानगी', audio: '' },
      explanation: {
        label:
          'हे यंत्र तुम्हाला तुमच्या तब्येतीबद्दल प्रश्न विचारेल आणि तुमची उत्तरे तुमच्या आवाजात नोंदवेल. तुमच्या जुन्या चिठ्ठ्या आणि अहवालांचे फोटोही वाचू शकते. ही माहिती आज तुम्हाला तपासणारे डॉक्टरच पाहतील. इतर कोणाशीही काहीही सामायिक केले जाणार नाही. तुम्ही नकार देऊ शकता. नकार दिला तरी तुम्ही नेहमीप्रमाणे डॉक्टरांना भेटू शकता.',
        audio:
          'कृपया लक्षपूर्वक ऐका. हे यंत्र तुम्हाला तुमच्या तब्येतीबद्दल प्रश्न विचारेल आणि तुमची उत्तरे तुमच्या आवाजात नोंदवेल. तुमच्या जुन्या चिठ्ठ्या आणि अहवालांचे फोटोही वाचू शकते. ही माहिती आज तुम्हाला तपासणारे डॉक्टरच पाहतील. इतर कोणाशीही काहीही सामायिक केले जाणार नाही. तुम्ही नकार देऊ शकता. नकार दिला तरी तुम्ही नेहमीप्रमाणे डॉक्टरांना भेटू शकता.',
      },
      playAgain: { label: 'पुन्हा ऐका', audio: '' },
      optHistory: { label: 'माझी आरोग्य माहिती नोंदवा', audio: 'माझी आरोग्य माहिती नोंदवा.' },
      optDocuments: { label: 'माझी जुनी कागदपत्रे वाचा', audio: 'माझी जुनी कागदपत्रे वाचा.' },
      optAbha: { label: 'हे माझ्या आभा नोंदीशी जोडा', audio: 'हे माझ्या आभा नोंदीशी जोडा.' },
      agree: { label: 'मी सहमत आहे', audio: 'मी सहमत आहे.' },
      decline: { label: 'मी सहमत नाही', audio: 'मी सहमत नाही.' },
      declinedTitle: { label: 'काही हरकत नाही', audio: 'काही हरकत नाही.' },
      declinedBody: {
        label: 'तुम्ही नेहमीप्रमाणे डॉक्टरांना भेटू शकता. कृपया काउंटरवर जा.',
        audio: 'तुम्ही नेहमीप्रमाणे डॉक्टरांना भेटू शकता. कृपया काउंटरवर जा.',
      },
    },
    complaint: {
      title: { label: 'आज तुम्हाला काय त्रास होतोय?', audio: 'आज तुम्हाला काय त्रास होतोय? तुम्ही बोलू शकता, किंवा चित्रावर दाबू शकता.' },
      head: { label: 'डोके', audio: 'डोके.' },
      chest: { label: 'छाती', audio: 'छाती.' },
      stomach: { label: 'पोट', audio: 'पोट.' },
      back: { label: 'पाठ', audio: 'पाठ.' },
      joints: { label: 'सांधे', audio: 'सांधे.' },
      skin: { label: 'त्वचा', audio: 'त्वचा.' },
      fever: { label: 'ताप', audio: 'ताप.' },
      breathing: { label: 'श्वास', audio: 'श्वास.' },
      other: { label: 'दुसरे काही', audio: 'दुसरे काही.' },
    },
    documents: {
      title: { label: 'तुमच्याकडे जुनी चिठ्ठी किंवा अहवाल आहे का?', audio: 'आज तुमच्याकडे जुनी चिठ्ठी किंवा अहवाल आहे का?' },
      yes: { label: 'होय, माझ्याकडे कागद आहेत', audio: 'होय, माझ्याकडे कागद आहेत.' },
      no: { label: 'नाही, पुढे जा', audio: 'नाही, पुढे जा.' },
      cameraTitle: { label: 'कागद चौकटीत धरा', audio: 'कागद सरळ करून चौकटीत धरा, मग गोल बटण दाबा.' },
      capture: { label: 'फोटो घ्या', audio: 'फोटो घ्या.' },
      addAnother: { label: 'आणखी एक जोडा', audio: 'आणखी एक कागद जोडा.' },
      done: { label: 'पूर्ण', audio: 'पूर्ण झाले.' },
      remove: { label: 'काढा', audio: 'काढले.' },
      cameraBlocked: {
        label: 'कॅमेरा उपलब्ध नाही. कृपया तुमचे कागद डॉक्टरांना दाखवा.',
        audio: 'कॅमेरा उपलब्ध नाही. कृपया तुमचे कागद डॉक्टरांना दाखवा.',
      },
    },
    confirm: {
      title: { label: 'तुम्ही सांगितलेले तपासा', audio: 'कृपया ऐका आणि तुम्ही काय सांगितले ते तपासा.' },
      correct: { label: 'होय, हे बरोबर आहे', audio: 'होय, हे बरोबर आहे.' },
      nothing: { label: 'काहीही नोंदवले गेले नाही', audio: 'काहीही नोंदवले गेले नाही.' },
    },
    done: {
      title: { label: 'धन्यवाद', audio: 'धन्यवाद.' },
      token: { label: 'तुमचा टोकन क्रमांक', audio: '' },
      room: { label: 'डॉक्टरांची खोली', audio: '' },
      wait: { label: 'कृपया थांबा. तुम्हाला बोलावले जाईल.', audio: 'कृपया थांबा. तुम्हाला बोलावले जाईल.' },
    },
    emergency: {
      patient: { label: 'कृपया लगेच आपत्कालीन काउंटरवर जा', audio: 'कृपया लगेच आपत्कालीन काउंटरवर जा. हा पडदा कर्मचाऱ्याला दाखवा.' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'तुम्ही अजून आहात का?', audio: 'तुम्ही अजून आहात का?' },
      continue: { label: 'होय, सुरू ठेवा', audio: 'होय, सुरू ठेवा.' },
      closing: { label: 'बंद होत आहे', audio: '' },
    },
    error: {
      title: { label: 'काहीतरी चूक झाली', audio: 'काहीतरी चूक झाली. कृपया कर्मचाऱ्याला बोलवा.' },
      body: { label: 'कृपया कर्मचाऱ्याला बोलवा.', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'पुन्हा सुरू करा', audio: '' },
    },
  },

  bn: {
    phase: {
      identity: { label: 'কয়েকটি প্রাথমিক তথ্য দিয়ে শুরু করি।', audio: '' },
      consent: { label: 'শুরু করার আগে আপনার সম্মতি দরকার।', audio: '' },
      chief_complaint: { label: 'আজ আপনার কী সমস্যা?', audio: '' },
      hpi: { label: 'এই সমস্যা সম্পর্কে আরও বলুন।', audio: '' },
      ros: { label: 'আপনার সার্বিক শরীর নিয়ে একটি ছোট প্রশ্ন।', audio: '' },
      past_medical: { label: 'আপনার দীর্ঘমেয়াদি রোগ বা আগে কোনো অস্ত্রোপচার হয়েছে?', audio: '' },
      drug_allergy: { label: 'আপনি কোনো ওষুধ খান কি, আর কোনো অ্যালার্জি আছে?', audio: '' },
      family: { label: 'আপনার পরিবারে কারও গুরুতর অসুখ আছে?', audio: '' },
      personal: { label: 'জীবনযাত্রা নিয়ে কয়েকটি প্রশ্ন।', audio: '' },
      documents: { label: 'আপনার কাছে পুরনো ব্যবস্থাপত্র বা পরীক্ষার রিপোর্ট আছে?', audio: '' },
      confirm: { label: 'শেষ করার আগে আপনার উত্তরগুলো দেখে নিন।', audio: '' },
    },
    common: {
      repeat: { label: 'আবার শুনুন', audio: 'এটি আবার শুনুন।' },
      listen: { label: 'শুনুন', audio: '' },
      stop: { label: 'থামান', audio: '' },
      back: { label: 'পিছনে', audio: 'পিছনে যাচ্ছি।' },
      next: { label: 'পরবর্তী', audio: 'পরবর্তী প্রশ্ন।' },
      yes: { label: 'হ্যাঁ', audio: 'হ্যাঁ।' },
      no: { label: 'না', audio: 'না।' },
      doneSpeaking: { label: 'বলা শেষ', audio: 'বলা শেষ হয়েছে।' },
      tapToSpeak: { label: 'বলতে চাপুন', audio: 'সবুজ বৃত্তে চাপ দিয়ে বলুন।' },
      tapOrType: {
        label: 'বলতে মাইকে চাপুন, বা এখানে লিখুন',
        audio: 'সবুজ বৃত্তে চাপ দিয়ে বলুন, বা আপনার উত্তর এখানে লিখুন।',
      },
      typeHere: {
        label: 'আপনার উত্তর এখানে লিখুন',
        audio: 'মাইক কাজ করছে না। অনুগ্রহ করে আপনার উত্তর এখানে লিখুন।',
      },
      listening: { label: 'শুনছি', audio: 'আমি শুনছি।' },
      oneMoment: { label: 'এক মুহূর্ত', audio: 'অনুগ্রহ করে এক মুহূর্ত অপেক্ষা করুন।' },
      understood: { label: 'আমরা যা বুঝেছি', audio: '' },
      moreFields: { label: '+{n} আরও', audio: '' },
      notSure: { label: 'নিশ্চিত নই — দয়া করে দেখুন', audio: '' },
      edit: { label: 'পরিবর্তন', audio: 'এই উত্তরটি পরিবর্তন করুন।' },
      micUnavailable: {
        label: 'আপনি উত্তর চেপেও বেছে নিতে পারেন',
        audio: 'মাইক কাজ করছে না। অনুগ্রহ করে আপনার উত্তর চেপে বেছে নিন।',
      },
    },
    idle: {
      begin: { label: 'শুরু করতে এখানে স্পর্শ করুন', audio: 'শুরু করতে পর্দা স্পর্শ করুন।' },
      subtitle: { label: 'আয়ুষ মন্ত্রক · বহির্বিভাগ', audio: '' },
    },
    language: {
      title: { label: 'আপনার ভাষা নির্বাচন করুন', audio: 'অনুগ্রহ করে আপনার ভাষা নির্বাচন করুন।' },
      greeting: { label: 'বাংলা', audio: 'নমস্কার। বাংলা নির্বাচন করা হয়েছে। চলুন শুরু করি।' },
    },
    identify: {
      title: { label: 'আপনার রেকর্ড খুঁজে নিই', audio: 'আপনার রেকর্ড খুঁজে নিই। অনুগ্রহ করে একটি বেছে নিন।' },
      abha: { label: 'আমার আভা নম্বর আছে', audio: 'আমার আভা নম্বর আছে।' },
      aadhaar: { label: 'আমার আধার আছে', audio: 'আমার আধার নম্বর আছে।' },
      newHere: { label: 'আমি এখানে নতুন', audio: 'আমি এখানে নতুন।' },
      abhaTitle: { label: 'আপনার আভা নম্বর লিখুন', audio: 'অনুগ্রহ করে সংখ্যা দিয়ে আপনার আভা নম্বর লিখুন।' },
      aadhaarTitle: { label: 'আপনার আধার নম্বর লিখুন', audio: 'অনুগ্রহ করে সংখ্যা দিয়ে আপনার আধার নম্বর লিখুন।' },
      checking: { label: 'পরীক্ষা করা হচ্ছে', audio: 'আপনার নম্বর পরীক্ষা করা হচ্ছে। এক মুহূর্ত।' },
      nameTitle: { label: 'আপনার নাম কী?', audio: 'আপনার নাম কী? আপনি বলতে পারেন বা লিখতে পারেন।' },
      ageTitle: { label: 'আপনার বয়স কত?', audio: 'আপনার বয়স কত? অনুগ্রহ করে সংখ্যা দিয়ে লিখুন।' },
      sexTitle: { label: 'অনুগ্রহ করে নির্বাচন করুন', audio: 'অনুগ্রহ করে একটি বেছে নিন।' },
      male: { label: 'পুরুষ', audio: 'পুরুষ।' },
      female: { label: 'মহিলা', audio: 'মহিলা।' },
      otherSex: { label: 'অন্যান্য', audio: 'অন্যান্য।' },
    },
    consent: {
      title: { label: 'আপনার অনুমতি', audio: '' },
      explanation: {
        label:
          'এই যন্ত্রটি আপনার স্বাস্থ্য সম্পর্কে প্রশ্ন করবে এবং আপনার উত্তর আপনার নিজের কণ্ঠে রেকর্ড করবে। এটি আপনার পুরনো প্রেসক্রিপশন ও রিপোর্টের ছবিও পড়তে পারে। এই তথ্য কেবল আজ যে ডাক্তার আপনাকে দেখবেন তিনিই দেখবেন। অন্য কারও সঙ্গে কিছু ভাগ করা হবে না। আপনি অস্বীকার করতে পারেন। অস্বীকার করলেও আপনি স্বাভাবিকভাবে ডাক্তারের সঙ্গে দেখা করতে পারবেন।',
        audio:
          'অনুগ্রহ করে মনোযোগ দিয়ে শুনুন। এই যন্ত্রটি আপনার স্বাস্থ্য সম্পর্কে প্রশ্ন করবে এবং আপনার উত্তর আপনার নিজের কণ্ঠে রেকর্ড করবে। এটি আপনার পুরনো প্রেসক্রিপশন ও রিপোর্টের ছবিও পড়তে পারে। এই তথ্য কেবল আজ যে ডাক্তার আপনাকে দেখবেন তিনিই দেখবেন। অন্য কারও সঙ্গে কিছু ভাগ করা হবে না। আপনি অস্বীকার করতে পারেন। অস্বীকার করলেও আপনি স্বাভাবিকভাবে ডাক্তারের সঙ্গে দেখা করতে পারবেন।',
      },
      playAgain: { label: 'আবার শুনুন', audio: '' },
      optHistory: { label: 'আমার স্বাস্থ্য তথ্য রেকর্ড করুন', audio: 'আমার স্বাস্থ্য তথ্য রেকর্ড করুন।' },
      optDocuments: { label: 'আমার পুরনো কাগজপত্র পড়ুন', audio: 'আমার পুরনো কাগজপত্র পড়ুন।' },
      optAbha: { label: 'এটি আমার আভা রেকর্ডের সঙ্গে যুক্ত করুন', audio: 'এটি আমার আভা রেকর্ডের সঙ্গে যুক্ত করুন।' },
      agree: { label: 'আমি সম্মত', audio: 'আমি সম্মত।' },
      decline: { label: 'আমি সম্মত নই', audio: 'আমি সম্মত নই।' },
      declinedTitle: { label: 'কোনো অসুবিধা নেই', audio: 'কোনো অসুবিধা নেই।' },
      declinedBody: {
        label: 'আপনি স্বাভাবিকভাবে ডাক্তারের সঙ্গে দেখা করতে পারেন। অনুগ্রহ করে কাউন্টারে যান।',
        audio: 'আপনি স্বাভাবিকভাবে ডাক্তারের সঙ্গে দেখা করতে পারেন। অনুগ্রহ করে কাউন্টারে যান।',
      },
    },
    complaint: {
      title: { label: 'আজ আপনার কী সমস্যা?', audio: 'আজ আপনার কী সমস্যা? আপনি বলতে পারেন, অথবা ছবিতে চাপ দিতে পারেন।' },
      head: { label: 'মাথা', audio: 'মাথা।' },
      chest: { label: 'বুক', audio: 'বুক।' },
      stomach: { label: 'পেট', audio: 'পেট।' },
      back: { label: 'পিঠ', audio: 'পিঠ।' },
      joints: { label: 'গাঁট', audio: 'গাঁট।' },
      skin: { label: 'ত্বক', audio: 'ত্বক।' },
      fever: { label: 'জ্বর', audio: 'জ্বর।' },
      breathing: { label: 'শ্বাস', audio: 'শ্বাস।' },
      other: { label: 'অন্য কিছু', audio: 'অন্য কিছু।' },
    },
    documents: {
      title: { label: 'আপনার কি পুরনো প্রেসক্রিপশন বা রিপোর্ট আছে?', audio: 'আজ আপনার কি পুরনো প্রেসক্রিপশন বা রিপোর্ট আছে?' },
      yes: { label: 'হ্যাঁ, আমার কাগজ আছে', audio: 'হ্যাঁ, আমার কাগজ আছে।' },
      no: { label: 'না, এড়িয়ে যান', audio: 'না, এড়িয়ে যান।' },
      cameraTitle: { label: 'কাগজটি বাক্সের ভিতরে ধরুন', audio: 'কাগজটি সোজা করে বাক্সের ভিতরে ধরুন, তারপর গোল বোতামে চাপ দিন।' },
      capture: { label: 'ছবি তুলুন', audio: 'ছবি তুলুন।' },
      addAnother: { label: 'আরেকটি যোগ করুন', audio: 'আরেকটি কাগজ যোগ করুন।' },
      done: { label: 'শেষ', audio: 'শেষ হয়েছে।' },
      remove: { label: 'সরান', audio: 'সরানো হয়েছে।' },
      cameraBlocked: {
        label: 'ক্যামেরা পাওয়া যাচ্ছে না। অনুগ্রহ করে আপনার কাগজ ডাক্তারকে দেখান।',
        audio: 'ক্যামেরা পাওয়া যাচ্ছে না। অনুগ্রহ করে আপনার কাগজ ডাক্তারকে দেখান।',
      },
    },
    confirm: {
      title: { label: 'আপনি যা বলেছেন তা দেখে নিন', audio: 'অনুগ্রহ করে শুনুন এবং আপনি যা বলেছেন তা দেখে নিন।' },
      correct: { label: 'হ্যাঁ, এটি ঠিক আছে', audio: 'হ্যাঁ, এটি ঠিক আছে।' },
      nothing: { label: 'কিছুই রেকর্ড হয়নি', audio: 'কিছুই রেকর্ড হয়নি।' },
    },
    done: {
      title: { label: 'ধন্যবাদ', audio: 'ধন্যবাদ।' },
      token: { label: 'আপনার টোকেন নম্বর', audio: '' },
      room: { label: 'ডাক্তারের ঘর', audio: '' },
      wait: { label: 'অনুগ্রহ করে অপেক্ষা করুন। আপনাকে ডাকা হবে।', audio: 'অনুগ্রহ করে অপেক্ষা করুন। আপনাকে ডাকা হবে।' },
    },
    emergency: {
      patient: { label: 'অনুগ্রহ করে এখনই জরুরি কাউন্টারে যান', audio: 'অনুগ্রহ করে এখনই জরুরি কাউন্টারে যান। এই পর্দাটি কর্মীকে দেখান।' },
      staff: { label: 'STAFF: red flag detected. Escort this patient to emergency triage immediately.', audio: '' },
      hold: { label: 'Staff: press and hold for 3 seconds to dismiss', audio: '' },
    },
    timeout: {
      title: { label: 'আপনি কি এখনও আছেন?', audio: 'আপনি কি এখনও আছেন?' },
      continue: { label: 'হ্যাঁ, চালিয়ে যান', audio: 'হ্যাঁ, চালিয়ে যান।' },
      closing: { label: 'বন্ধ হচ্ছে', audio: '' },
    },
    error: {
      title: { label: 'কিছু ভুল হয়েছে', audio: 'কিছু ভুল হয়েছে। অনুগ্রহ করে কর্মীকে ডাকুন।' },
      body: { label: 'অনুগ্রহ করে কর্মীকে ডাকুন।', audio: '' },
      staff: { label: 'STAFF: kiosk error. Restart the session from the screen below.', audio: '' },
      restart: { label: 'আবার শুরু করুন', audio: '' },
    },
  },
};

const EMPTY = { label: '', audio: '' };

/**
 * Look up one string.
 * @param {string} lang  language code, e.g. 'hi'
 * @param {string} path  'screen.key', e.g. 'consent.agree'
 * @returns {{label: string, audio: string}}
 */
export function t(lang, path) {
  const [screen, key] = path.split('.');
  const entry = strings[lang]?.[screen]?.[key] ?? strings[DEFAULT_LANG]?.[screen]?.[key];
  if (!entry) {
    console.warn(`[i18n] missing string: ${path}`);
    return EMPTY;
  }
  return entry;
}

/* ------------------------------------------------------- bilingual lookup */

// Reverse index: a rendered label in some language -> the English label for the
// same entry. Built once from `strings` above.
//
// This exists so the bilingual rule can be applied in the shared components
// rather than edited into all ~48 places a screen renders a label. A screen
// keeps passing a plain string; the component finds its English counterpart.
//
// Text with no entry here — an interview question or option, which the API
// sends already translated — simply returns undefined and renders once. That
// is correct: there is no English counterpart on the client to show.
const REVERSE = (() => {
  const index = {};
  for (const [lang, screens] of Object.entries(strings)) {
    if (lang === DEFAULT_LANG) continue;
    const map = new Map();
    for (const [screen, entries] of Object.entries(screens)) {
      for (const [key, entry] of Object.entries(entries)) {
        const english = strings[DEFAULT_LANG]?.[screen]?.[key]?.label;
        if (entry?.label && english && entry.label !== english) {
          // First writer wins. A duplicate label in one language means the two
          // entries say the same thing, so either English rendering is right.
          if (!map.has(entry.label)) map.set(entry.label, english);
        }
      }
    }
    index[lang] = map;
  }
  return index;
})();

/** The English label matching `text` in `lang`, or undefined if unknown. */
export function englishFor(text, lang) {
  if (!text || lang === DEFAULT_LANG) return undefined;
  return REVERSE[lang]?.get(String(text));
}
