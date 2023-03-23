from __future__ import annotations

import sys

from misc.obsSubtitles import *
from misc.translation import *
import helper

import os

from ttsProviders.ElevenlabsProvider import ElevenlabsProvider
from ttsProviders.PyttsxProvider import PyttsxProvider
from ttsProviders.__TTSProviderAbstract import TTSProvider

from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
from speechRecognition.WhisperProvider import WhisperProvider
from speechRecognition.VoskProvider import VoskProvider
from speechRecognition.AzureProvider import AzureProvider

#The whisper API does not return language information, so we use googletrans to detect the language from the text.
#Won't be super accurate, but it should be pretty fast.
import googletrans

#THESE IMPORTS ARE NOT UNUSED. recasepunc does some weird reflection stuff.
from misc.recasepunc import CasePuncPredictor, WordpieceTokenizer
dummyVar:CasePuncPredictor
dummyVar2:WordpieceTokenizer



srProvider:SpeechRecProvider
def main():
    helper.show_text("Voice recognition will start once you click OK...")
    print("Recognition started...")
    srProvider.recognize_loop()



# I'll just use googletrans in that case.
def process_text(recognizedText:str, language):
    # If you want to do anything with the text (like sending it off to chatGPT and playing back the response instead) this is where you do it.
    recognizedText = recognizedText.strip()
    if recognizedText != "":    #Ignore empty output
        translatedText = translate_if_needed(recognizedText, language)
        #translatedText contains the text in english.
        print("Recognized and translated text: " + translatedText)

        helper.ttsProvider.synthesizeAndPlayAudio(translatedText, helper.chosenOutput)
        if helper.subtitlesEnabled:
            subtitle_update(translatedText)
    print("\nListening for voice input...\n")



def setup():
    #if not helper.useGUI:
    helper.setup_config()

    configQuestions = dict()
    outputDeviceQuestion = {
        "widget_type": "list",
        "options": helper.get_list_of_portaudio_devices("output"),
        "label": "Output Device"
    }

    srProviderQuestion = {
        "widget_type": "list",
        "options": ["Vosk", "Whisper", "Azure"],
        "descriptions": [
               "Good accuracy, local and fast."
               "\nDoes not include punctuation by default but includes the option to use recasepunc to add it, which does make it heavier to run."
               "\nI find it to be a very good balance of quality+speed, at least when it comes to english."
               "\nIt's worth noting that it can only support 1 language at a time (so you will be unable to speak using multiple languages)."
               "\nIn addition, its language support is limited by what models are available, especially for recasepunc."
               "\nIf you want to speak english and stick with something local that's still pretty fast, use this.\n",



               "Can either can either be used locally or online through their API (at 0.006$/minute of speech)."
               "\nThe local version offers a few different model sizes, whereas the API always uses the largest."
               "\nAttempting to run the largest model size locally, assuming you even have an NVIDIA GPU with enough VRAM for it, will be pretty slow."
               "\nI recommend sticking to the medium one at most, but you should try it and see how well it works on your machine."
               "\nSupports a variety of languages, more languages are supported by the local version than the API however."
               "\nIt does not require you to specify which language you will be speaking.\n",


               "Great accuracy, online, supports a bunch of languages."
               "\nIncludes 5 hours free per month, following speech is billed at 1$/hour."
               "\nThat's 0.016$/minute of speech, which is roughly 2.5x as much as Whisper."
               "\nIt supports speaking using multiple languages, but you will have to narrow it down to 10 maximum."
               "\nThis is the best option if you need something online but don't want to pay, once you go over the 5 hours/month you should switch to Whisper for a cheaper price.\n"],
        "label":"Speech Recognition Provider"
    }

    ttsProviderQuestion = {
        "widget_type": "list",
        "options": ["ElevenLabs - High quality, online, paid", "pyttsx3 - Low quality, local, free"],
        "label": "Text To Speech Provider"
    }

    miscConfig = helper.get_misc_config()

    configQuestions["output_device"] = outputDeviceQuestion
    configQuestions["speech_provider"] = srProviderQuestion
    configQuestions["tts_provider"] = ttsProviderQuestion

    userInput = helper.ask_fetch_from_and_update_config(configQuestions, miscConfig, "General settings")



    chosenOutputInfo = helper.get_portaudio_device_info_from_name(userInput["output_device"])
    helper.chosenOutput = chosenOutputInfo["index"]
    subtitle_setup()
    translation_setup()
    global srProvider
    availableSRProviders: list[SpeechRecProvider] = [VoskProvider, WhisperProvider, AzureProvider]
    chosenSRProviderClass:SpeechRecProvider = availableSRProviders[srProviderQuestion["options"].index(userInput["speech_provider"])]
    srProvider = chosenSRProviderClass()


    #Make the user choose from a provider and ensure that the config data field is present in the config file.
    availableTTSProviders:list[TTSProvider] = [ElevenlabsProvider, PyttsxProvider]
    chosenTTSProviderClass:TTSProvider = availableTTSProviders[ttsProviderQuestion["options"].index(userInput["tts_provider"])]
    helper.ttsProvider = chosenTTSProviderClass()



if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cli":
            helper.useGUI = False   #Is true by default

    # Make sure the default folders exist...
    modelDir = os.path.join(os.getcwd(), "models")
    if not os.path.isdir(modelDir):
        os.mkdir(modelDir)

    voskModelsDir = os.path.join(modelDir, "vosk")
    if not os.path.isdir(voskModelsDir):
        os.mkdir(voskModelsDir)

    recasepuncModelsDir = os.path.join(modelDir, "recasepunc")
    if not os.path.isdir(recasepuncModelsDir):
        os.mkdir(recasepuncModelsDir)

    setup()
    main()
