import datetime
from typing import Optional

import helper
import googletrans
import deepl
googleTranslator:googletrans.Translator
deeplTranslator:Optional[deepl.Translator] = None
targetLanguage = "en"
def translation_setup():
    translationConfigInputs = dict()

    translationEngineInput = {
        "widget_type":"list",
        "options":["Google Translate","DeepL"],
        "label":"Translation engine"
    }

    translationLanguageInput = {
        "widget_type": "list",
        "label": "TTS output language",
        "options":["en","de","pl","es","it","fr","pt","hi"],
        "descriptions":["All recognized text from your speech will be translated\n"
                        "into this language before being converted into the TTS output."]
    }

    deeplAPIKeyInput = {
        "widget_type": "textbox",
        "label": "DeepL API Key",
        "hidden": True
    }

    if not helper.useGUI:
        if helper.choose_yes_no("Would you like to skip the translation setup?"):
            return

    tlConfig = helper.get_translation_config()

    translationConfigInputs["deepl_api_key"] = deeplAPIKeyInput
    translationConfigInputs["engine"] = translationEngineInput
    translationConfigInputs["language"] = translationLanguageInput

    global deeplTranslator, googleTranslator
    while True:
        result = helper.ask_fetch_from_and_update_config(translationConfigInputs, tlConfig,"Translation config")
        global targetLanguage
        targetLanguage = result["language"]
        if result["engine"] == "DeepL":
            deeplTranslator = deepl.Translator(result["deepl_api_key"]).set_app_info("speech_to_speech_by_lugia","2.0.0")
            try:
                deeplTranslator.get_usage()
                break
            except deepl.AuthorizationException:
                if not helper.choose_yes_no("Authorization failed! API Key incorrect or expired. Try again?"):
                    deeplTranslator = None
                    break
        else:
            break

    googleTranslator = googletrans.Translator()
def translate_if_needed(text:str, language:str) -> str:
    tlStartTime = datetime.datetime.now()
    print("\nLanguage recieved from process_text: " + str(language))
    if language is None:
        language = googleTranslator.detect(text).lang
        print("Detected language with googletrans: " + language)
        print(f"Time loss due to language detection: {(datetime.datetime.now()-tlStartTime).total_seconds()}s")
        tlStartTime = datetime.datetime.now()

    language = language.lower()  # Ensure it's in lowercase.

    #Check if it's already in the target language
    if "-" in language:
        if language[:language.index("-")] == targetLanguage:
            return text
    else:
        if language == targetLanguage:
            return text

    if deeplTranslator is not None:
        supportedLanguages = deeplTranslator.get_source_languages()
        supportedLanguageCodes = list()
        for lang in supportedLanguages:
            supportedLanguageCodes.append(lang.code.lower())

        if language in supportedLanguageCodes or ("-" in language and language[:language.index("-")] in supportedLanguageCodes):
            print("Translating text using deepl...")
            deepLTargetLang = targetLanguage.upper()

            #Ensure we don't run into trouble with the deprecated language codes
            if deepLTargetLang == "EN":
                deepLTargetLang = "EN-US"
            if deepLTargetLang == "PT":
                deepLTargetLang = "PT-BR"

            result = deeplTranslator.translate_text(text, target_lang=deepLTargetLang)
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text

    print("Translating text using googletrans...")
    if language not in googletrans.LANGCODES:
        if "-" in language and language[:language.index("-")] in googletrans.LANGCODES:
            language = language[:language.index("-")]
            result = googleTranslator.translate(text, dest=targetLanguage, src=language)
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text
        else:
            result = googleTranslator.translate(text, dest=targetLanguage)
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text
    else:
        result = googleTranslator.translate(text, dest=targetLanguage, src=language)
        print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
        return result.text

