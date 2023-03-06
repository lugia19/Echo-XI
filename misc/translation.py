from typing import Optional

import helper
import googletrans
import deepl
googleTranslator:googletrans.Translator
deeplTranslator:Optional[deepl.Translator] = None
def translation_setup():
    print("Note: Regardless of which language you choose when initializing a speech provider, the text to speech output will ALWAYS be in english.")
    global deeplTranslator, googleTranslator
    if helper.choose_yes_no("Would you like to use DeepL to translate the languages it supports?"):
        deeplConfig = helper.get_deepl_config()
        if deeplConfig["api_key"] == "":
            deeplConfig["api_key"] = input("Please input your DeepL API key.")
            helper._configData["deepl_settings"]["api_key"] = deeplConfig["api_key"]
            helper.update_config_file()

        deeplTranslator = deepl.Translator(deeplConfig["api_key"]).set_app_info("speech_to_speech_by_lugia","2.0.0")

    googleTranslator = googletrans.Translator()
def translate_if_needed(text:str, language:str) -> str:
    print("Language recieved from process_text: " + str(language))
    if language is None:
        language = googleTranslator.detect(text).lang
        print("Detected language with googletrans: " + language)

    language = language.lower()  # Ensure it's in lowercase.

    if language == "en":
        return text

    if deeplTranslator is not None:
        supportedLanguages = deeplTranslator.get_source_languages()
        supportedLanguageCodes = list()
        for lang in supportedLanguages:
            supportedLanguageCodes.append(lang.code.lower())

        if language in supportedLanguageCodes or ("-" in language and language[:language.index("-")] in supportedLanguageCodes):
            print("Translating text using deepl...")
            result = deeplTranslator.translate_text(text, target_lang="EN-US")
            return result.text

    print("Translating text using googletrans...")
    if language not in googletrans.LANGCODES:
        if "-" in language and language[:language.index("-")] in googletrans.LANGCODES:
            language = language[:language.index("-")]
            result = googleTranslator.translate(text, dest="en", src=language)
            return result.text
        else:
            result = googleTranslator.translate(text, dest="en")
            return result.text
    else:
        result = googleTranslator.translate(text, dest="en", src=language)
        return result.text

