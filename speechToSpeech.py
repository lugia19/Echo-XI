from __future__ import annotations

import vosk

from misc.obsSubtitles import *
from misc.recasepuncCaller import *
import helper

import io
import os
import wave
import pyaudio
from vosk import Model, KaldiRecognizer

from ttsProviders.ElevenlabsProvider import ElevenlabsProvider
from ttsProviders.PyttsxProvider import PyttsxProvider
from ttsProviders.__TTSProviderAbstract import TTSProvider

voskModel:vosk.Model        #TODO: Rework this to use the speechsynthesis lib
ttsProvider:TTSProvider

def main():
    subtitlesEnabled = helper.yesNo("Enable text output for OBS websocket?")

    if subtitlesEnabled:
        subtitle_setup(helper.configData["obs_host"], helper.configData["obs_port"], helper.configData["obs_password"])

    recasepuncEnabled =helper.yesNo("Would you like to enable case/punctuation detection? (Improves AI voice and subtitles)")

    if recasepuncEnabled:
        recasepunc_setup()

    pyAudio = pyaudio.PyAudio()
    info = pyAudio.get_host_api_info_by_index(0)
    totalNumDevices = info.get('deviceCount')
    inputDeviceIndexes = []
    outputDeviceIndexes = []
    for i in range(0, totalNumDevices):
        if (pyAudio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            inputDeviceIndexes.append(i)
        elif (pyAudio.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            outputDeviceIndexes.append(i)

    chosenInput = -1
    for deviceIndex in inputDeviceIndexes:
        print("Input Device id ", deviceIndex, " - ", pyAudio.get_device_info_by_host_api_device_index(0, deviceIndex).get('name'))
    while not(chosenInput in inputDeviceIndexes):
        try:
            chosenInput = int(input("Please select which input device you'd like to use."))
        except:
            print("Not a valid number.")
    print("\nChosen input info: " + str(pyAudio.get_device_info_by_host_api_device_index(0, chosenInput))+"\n")
    inputRate = int(pyAudio.get_device_info_by_host_api_device_index(0, chosenInput)["defaultSampleRate"])
    try:
        recognizer = KaldiRecognizer(voskModel, inputRate)
    except:
        print("Could not open model. Did you remember to double escape the backslashes in the config?")
        return

    micStream = pyAudio.open(format=pyaudio.paInt16, channels=1, rate=inputRate, input=True, frames_per_buffer=8192, input_device_index=chosenInput)


    for deviceIndex in outputDeviceIndexes:
        print("Output Device id ", deviceIndex, " - ", pyAudio.get_device_info_by_host_api_device_index(0, deviceIndex).get('name'))
    chosenOutput = -1
    while not(chosenOutput in outputDeviceIndexes):
        try:
            chosenOutput = int(input("Please select which output device you'd like to use."))
        except:
            print("Not a valid number.")
    print("\nChosen output info: " + str(pyAudio.get_device_info_by_host_api_device_index(0, chosenOutput))+"\n")

    #We don't have the info about the files in the config.json file, let's add it by getting a test audio.
    ttsProviderConfig = helper.configData["ttsConfig"][ttsProvider.__class__.__name__]
    if "sampwidth" not in ttsProviderConfig:
        wavTempFile = io.BytesIO(ttsProvider.synthesizeToWavBytes("A"))
        wf = wave.open(wavTempFile, "rb")
        ttsProviderConfig["sampwidth"] = wf.getsampwidth()
        ttsProviderConfig["channels"] = wf.getnchannels()
        ttsProviderConfig["framerate"] = wf.getframerate()
        helper.updateConfigFile()

    outputStream = pyAudio.open(format=pyAudio.get_format_from_width(ttsProviderConfig["sampwidth"]), channels=ttsProviderConfig["channels"], rate=ttsProviderConfig["framerate"], output=True, output_device_index=chosenOutput)
    print("\nListening for voice input...\n")
    while micStream.is_active():
        data = micStream.read(4096, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            recognizedText = recognizer.Result()[14:-3]
            if recognizedText != "":
                print("Recognized text: " + recognizedText)
                if recasepuncEnabled:
                    recognizedText = recasepunc_parse(recognizedText)
                wavTempFile = io.BytesIO(ttsProvider.synthesizeToWavBytes(recognizedText))
                if wavTempFile is not None:
                    if subtitlesEnabled:
                        subtitle_update(recognizedText)
                    print("Playing back audio...")
                    outputStream.write(wavTempFile.read())
                    print("\nListening for voice input...\n")



def setup():
    helper.setupConfig()
    #TODO: Change this from using only vosk to the other library
    if helper.configData["vosk_model_path"] != "":
        voskModelPath = helper.configData["vosk_model_path"]
    else:
        voskModelPath = findVoskModelInWorkingDir()

    global voskModel
    voskModel = Model(voskModelPath)


    #Make the user choose from a provider and ensure that the config data field is present in the config file.
    global ttsProvider
    availableProviders = [ElevenlabsProvider, PyttsxProvider]
    options = ["ElevenLabs - High quality, online, paid",
               "pyttsx3 - Low quality, local, free"]
    chosenProviderClass:ttsProvider = availableProviders[options.index(helper.chooseFromListOfStrings("Please choose a TTS provider.", options))]

    if chosenProviderClass.__name__ not in helper.configData["ttsConfig"]:
        helper.configData["ttsConfig"][chosenProviderClass.__name__] = dict()
        helper.updateConfigFile()

    ttsProvider = chosenProviderClass()

#This function is called if the vosk model isn't overridden, to try and find it in the working dir.
def findVoskModelInWorkingDir() -> str:
    voskModelPath = None
    print("Vosk model path not set in config, checking if there is one in the working directory...")
    eligibleDirectories = list()
    for directory in os.listdir(os.getcwd()):
        if os.path.isdir(directory) and "vosk-model-" in directory:
            eligibleDirectories.append(directory)
    if len(eligibleDirectories) == 0:
        print("Could not automatically determine location of vosk model, please either put it in the same directory as the script or set the location in config.json")
        exit()
    elif len(eligibleDirectories) == 1:
        voskModelPath = eligibleDirectories[0]
    else:
        voskModelPath = helper.chooseFromListOfStrings("Found multiple eligible vosk models. Please choose one.", eligibleDirectories)
    return voskModelPath

if __name__ == '__main__':
    setup()
    main()
