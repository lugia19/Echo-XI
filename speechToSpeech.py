from __future__ import annotations
from misc.obsSubtitles import *
from misc.recasepuncCaller import *
import helper

import os
import pyaudio

from ttsProviders.ElevenlabsProvider import ElevenlabsProvider
from ttsProviders.PyttsxProvider import PyttsxProvider
from ttsProviders.__TTSProviderAbstract import TTSProvider

from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
from speechRecognition.WhisperProvider import WhisperProvider
from speechRecognition.VoskProvider import VoskProvider
from speechRecognition.AzureProvider import AzureProvider

srProvider:SpeechRecProvider
def main():
    helper.subtitlesEnabled = helper.yesNo("Enable text output for OBS websocket?")

    if helper.subtitlesEnabled:
        subtitle_setup(helper.configData["obs_host"], helper.configData["obs_port"], helper.configData["obs_password"])

    recasepuncEnabled = helper.yesNo("Would you like to enable case/punctuation detection? (Improves AI voice and subtitles)")

    if recasepuncEnabled:
        recasepunc_setup()

    pyABackend = pyaudio.PyAudio()
    defaultHostAPI = pyABackend.get_default_host_api_info()

    inputDeviceNames = list()

    for i in range(defaultHostAPI["deviceCount"]):
        device = pyABackend.get_device_info_by_host_api_device_index(defaultHostAPI["index"], i)
        if device["maxInputChannels"] > 0:
            inputDeviceNames.append(device["name"] + " - " + str(device["index"]))

    outputDeviceNames = list()

    for i in range(defaultHostAPI["deviceCount"]):
        device = pyABackend.get_device_info_by_host_api_device_index(defaultHostAPI["index"], i)
        if device["maxOutputChannels"] > 0:
            outputDeviceNames.append(device["name"] + " - " + str(device["index"]))


    chosenInput = helper.chooseFromListOfStrings("Please choose your input device.", inputDeviceNames)
    chosenInput = int(chosenInput[chosenInput.rfind(" - ")+3:])
    chosenInputInfo = pyABackend.get_device_info_by_index(chosenInput)
    print("\nChosen input info: " + str(chosenInputInfo)+"\n")

    try:
        srProvider.setup_recognition(chosenInputInfo)
    except:
        print("Error setting up speech recognition.")
        return

    helper.chosenOutput = helper.chooseFromListOfStrings("Please choose your output device.", outputDeviceNames)
    helper.chosenOutput = int(helper.chosenOutput[helper.chosenOutput.rfind(" - ") + 3:])
    chosenOutputInfo = pyABackend.get_device_info_by_index(helper.chosenOutput)
    print("\nChosen input info: " + str(chosenOutputInfo) + "\n")

    print("\nListening for voice input...\n")
    srProvider.recognize_loop()


def process_text(recognizedText:str):
    helper.ttsProvider.synthesizeAndPlayAudio(recognizedText, helper.chosenOutput)
    if helper.subtitlesEnabled:
        subtitle_update(recognizedText)
    print("\nListening for voice input...\n")



def setup():
    helper.setupConfig()

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
    chosenSRProviderClass:SpeechRecProvider = availableSRProviders[options.index(helper.chooseFromListOfStrings("Please choose a speech recognition provider.", options))]

    if chosenSRProviderClass.__name__ not in helper.configData["ttsConfig"]:
        helper.configData["ttsConfig"][chosenSRProviderClass.__name__] = dict()
        helper.updateConfigFile()

    srProvider = chosenSRProviderClass()


    #Make the user choose from a provider and ensure that the config data field is present in the config file.
    availableTTSProviders:list[TTSProvider] = [ElevenlabsProvider, PyttsxProvider]
    options = ["ElevenLabs - High quality, online, paid",
               "pyttsx3 - Low quality, local, free"]
    chosenTTSProviderClass:TTSProvider = availableTTSProviders[options.index(helper.chooseFromListOfStrings("Please choose a TTS provider.", options))]

    if chosenTTSProviderClass.__name__ not in helper.configData["ttsConfig"]:
        helper.configData["ttsConfig"][chosenTTSProviderClass.__name__] = dict()
        helper.updateConfigFile()

    helper.ttsProvider = chosenTTSProviderClass()
    print("")

if __name__ == '__main__':
    setup()
    main()
