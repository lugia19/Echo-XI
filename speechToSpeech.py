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



def process_text(recognizedText:str):
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

    global srProvider
    availableSRProviders:list[SpeechRecProvider] = [VoskProvider, WhisperProvider, AzureProvider]
    options = ["Vosk - Good accuracy, local, fast",
               "Whisper - Great accuracy, local, slow",
               "Azure - Great accuracy, online, fast"]
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
