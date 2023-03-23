import datetime
from typing import Optional

import helper
import googletrans
import deepl
googleTranslator:googletrans.Translator
deeplTranslator:Optional[deepl.Translator] = None
def translation_setup():
    translationConfigInputs = dict()
    deeplEnabledInput = {
        "widget_type": "checkbox",
        "label": "Enable DeepL translation",
        "description": "Uses DeepL to translate your speech (if it's in a support language) into English. Otherwise it uses google translate."
    }

    deeplAPIKeyInput = {
        "widget_type": "textbox",
        "label": "DeepL API Key",
        "hidden": True
    }

    deeplConfig = helper.get_deepl_config()

    translationConfigInputs["deepl_api_key"] = deeplAPIKeyInput
    translationConfigInputs["enabled"] = deeplEnabledInput

    global deeplTranslator, googleTranslator
    while True:
        result = helper.ask_fetch_from_and_update_config(translationConfigInputs, deeplConfig,"Translation config")
        if result["enabled"]:
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

    if language == "en" or language == "en-us" or language == "en-gb":
        return text

    if deeplTranslator is not None:
        supportedLanguages = deeplTranslator.get_source_languages()
        supportedLanguageCodes = list()
        for lang in supportedLanguages:
            supportedLanguageCodes.append(lang.code.lower())

        if language in supportedLanguageCodes or ("-" in language and language[:language.index("-")] in supportedLanguageCodes):
            print("Translating text using deepl...")
            result = deeplTranslator.translate_text(text, target_lang="EN-US")
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text

    print("Translating text using googletrans...")
    if language not in googletrans.LANGCODES:
        if "-" in language and language[:language.index("-")] in googletrans.LANGCODES:
            language = language[:language.index("-")]
            result = googleTranslator.translate(text, dest="en", src=language)
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text
        else:
            result = googleTranslator.translate(text, dest="en")
            print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
            return result.text
    else:
        result = googleTranslator.translate(text, dest="en", src=language)
        print(f"Time loss due to translation: {(datetime.datetime.now() - tlStartTime).total_seconds()}s")
        return result.text

