from __future__ import annotations
from misc.obsSubtitles import *
import helper

import os

from ttsProviders.ElevenlabsProvider import ElevenlabsProvider
from ttsProviders.PyttsxProvider import PyttsxProvider
from ttsProviders.__TTSProviderAbstract import TTSProvider

from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
from speechRecognition.WhisperProvider import WhisperProvider
from speechRecognition.VoskProvider import VoskProvider
from speechRecognition.AzureProvider import AzureProvider

#THESE IMPORTS ARE NOT UNUSED. recasepunc does some weird reflection stuff.
from misc.recasepunc import CasePuncPredictor, WordpieceTokenizer
dummyVar:CasePuncPredictor
dummyVar2:WordpieceTokenizer



srProvider:SpeechRecProvider
def main():
    helper.subtitlesEnabled = helper.choose_yes_no("Enable text output for OBS websocket?")

    if helper.subtitlesEnabled:
        obs_config = helper.get_obs_config()
        subtitle_setup(obs_config["obs_host"], obs_config["obs_port"], obs_config["obs_password"])

    chosenOutputInfo = helper.select_portaudio_device("output")
    helper.chosenOutput = chosenOutputInfo["index"]

    print("\nListening for voice input...\n")
    srProvider.recognize_loop()


#TODO: Make whisper and azure pass the language of the audio as part of the call to process_text.
def process_text(recognizedText:str, language="UNKNOWN"):
    # If you want to do anything with the text (like sending it off to chatGPT and playing back the response instead) this is where you do it.
    if recognizedText != "":    #Ignore empty output
        #TODO: This is where we detect if the text is NOT english. If it isn't, we translate with deepl (or googletrans if the language isn't supported by deepl or no key was provided).

        helper.ttsProvider.synthesizeAndPlayAudio(recognizedText, helper.chosenOutput)
        if helper.subtitlesEnabled:
            subtitle_update(recognizedText)
    print("\nListening for voice input...\n")



def setup():
    helper.setup_config()

    modelDir = os.path.join(os.getcwd(),"models")
    if not os.path.isdir(modelDir):
        os.mkdir(modelDir)

    voskModelsDir = os.path.join(modelDir,"vosk")
    if not os.path.isdir(voskModelsDir):
        os.mkdir(voskModelsDir)

    #The reason why I use vosk regardless to detect when the user begins/ends speaking is because whisper actually fails to do so sometimes.
    #It's better to let vosk handle it then pass the audio off to the speech recognition provider.
    voskVoiceDetectModelPath = os.path.join(voskModelsDir,"vosk-model-small-en-us-0.15")
    if not os.path.isdir(voskVoiceDetectModelPath):
        print("Please download the \"small-en-us\" vosk model and place it in " + voskVoiceDetectModelPath)
        print("It is required for voice detection.")
        exit(1)

    print("Note: Regardless of which language you choose when initializing a speech provider, the text to speech output will ALWAYS be in english.")
    if helper.choose_yes_no("Would you like to enable DeepL as a translation engine? You will need to provide your own API key. If you choose no, google translate will be used instead."):
        pass        #TODO: THIS

    global srProvider
    availableSRProviders:list[SpeechRecProvider] = [VoskProvider, WhisperProvider, AzureProvider]
    options = ["Vosk"
               "\nGood accuracy, local and fast."
               "\nDoes not include punctuation by default but includes the option to use recasepunc to add it, which does make it heavier to run."
               "\nI find it to be a very good balance of quality+speed, at least when it comes to english."
               "\nIt's worth noting that it can only support 1 language at a time (so you will be unable to speak using multiple languages)."
               "\nIn addition, its language support is limited by what models are available, especially for recasepunc."
               "\nIf you want to speak english and stick with something local that's still pretty fast, use this.\n",


               "Whisper"
               "\nCan either can either be used locally or online through their API (at 0.006$/minute of speech)."
               "\nThe local version offers a few different model sizes, whereas the API always uses the largest."
               "\nAttempting to run the largest model size locally, assuming you even have an NVIDIA GPU with enough VRAM for it, will be pretty slow."
               "\nI recommend sticking to the medium one at most, but you should try it and see how well it works on your machine."
               "\nSupports a variety of languages, more languages are supported by the local version than the API however."
               "\nIt does not require you to specify which language you will be speaking.\n",

               "Azure"
               "\nGreat accuracy, online, supports a bunch of languages."
               "\nIncludes 5 hours free per month, following speech is billed at 1$/hour."
               "\nThat's 0.016$/minute of speech, which is roughly 2.5x as much as Whisper."
               "\nIt supports speaking using multiple languages, but you will have to narrow it down to 10 maximum."
               "\nThis is the best option if you need something online but don't want to pay, once you go over the 5 hours/month you should switch to Whisper for a cheaper price.\n"]
    chosenSRProviderClass:SpeechRecProvider = availableSRProviders[options.index(helper.choose_from_list_of_strings("Please choose a speech recognition provider.", options))]

    srProvider = chosenSRProviderClass()


    #Make the user choose from a provider and ensure that the config data field is present in the config file.
    availableTTSProviders:list[TTSProvider] = [ElevenlabsProvider, PyttsxProvider]
    options = ["ElevenLabs - High quality, online, paid",
               "pyttsx3 - Low quality, local, free (ONLY OUTPUTS TO DEFAULT PLAYBACK DEVICE!)"]
    chosenTTSProviderClass:TTSProvider = availableTTSProviders[options.index(helper.choose_from_list_of_strings("Please choose a TTS provider.", options))]

    helper.ttsProvider = chosenTTSProviderClass()
    print("")

if __name__ == '__main__':
    setup()
    main()
