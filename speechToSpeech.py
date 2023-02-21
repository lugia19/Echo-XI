from __future__ import annotations

import io
import json
import os
import textwrap
import wave
from typing import Optional
import pyaudio
from elevenlabslib import *
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

import obsws_python as obs
#Important! The wordpiecetokenizer import ISN'T UNUSED! DON'T TOUCH IT!
from recasepunc import CasePuncPredictor, WordpieceTokenizer

configData = {}
ttsVoice = {}
voskModel = {}
def yesNo(prompt) -> bool:
    print(prompt)
    userInput = ""
    while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
        userInput = input("y/n?")
    return userInput[0].lower() == "y"

def getNumber(prompt, minValue, maxValue) -> int:
    print(prompt)
    chosenVoiceIndex = -1
    while not (minValue <= chosenVoiceIndex <= maxValue):
        try:
            chosenVoiceIndex = int(input("Please choose a number.\n"))
        except:
            print("Not a valid number.")
    return chosenVoiceIndex

def main():
    subtitleEnable = yesNo("Enable text output for OBS websocket?")
    recasePuncEnable = yesNo("Would you like to enable case/punctuation detection? (Improves AI voice and subtitles)")

    if recasePuncEnable:
        repuncModelPath = ""
        if configData["repunc_model_path"] == "":
            print("Recase model path not set in config, checking if there is one in the working directory...")
            eligibleDirectories = list()
            for directory in os.listdir(os.getcwd()):
                if os.path.isdir(directory) and "vosk-recasepunc-" in directory:
                    eligibleDirectories.append(directory)
            if len(eligibleDirectories) == 0:
                print("Could not automatically determine location of recasepunc model, please either put it in the same directory as the script or set the location in config.json")
                exit()
            elif len(eligibleDirectories) == 1:
                repuncModelPath = eligibleDirectories[0]
                repuncModelPath = os.path.join(repuncModelPath, "checkpoint")
            else:
                print("Found multiple eligible repunc models.")
                i = 0
                for directory in eligibleDirectories:
                    print(str(i + 1) + ") " + directory)
                    i += 1
                chosenDirIndex = getNumber("Please choose one.", minValue=1, maxValue=len(eligibleDirectories)) - 1
                repuncModelPath = eligibleDirectories[chosenDirIndex]
                repuncModelPath = os.path.join(repuncModelPath, "checkpoint")
        else:
            repuncModelPath = configData["repunc_model_path"]

        predictor = CasePuncPredictor(repuncModelPath, lang="en", flavor="bert-base-uncased")

    if subtitleEnable:
        obsPort = configData["obs_port"]
        cl = obs.ReqClient(host="localhost", port=obsPort, password=configData["obs_password"])
        currentScene = cl.get_current_program_scene().current_program_scene_name
        print(currentScene)
        itemList = cl.get_scene_item_list(currentScene).scene_items
        textItem = None
        for item in itemList:
            if item["inputKind"] == "text_gdiplus_v2":
                if yesNo("Found text item " + item["sourceName"] + ", use it for subtitles?"):
                    textItem = item
                    break
        if textItem is None:
            input("No text item found or selected in current scene. Press enter to exit...")
            return
        settings = {"text": ""}
        #Clean whatever text was there before
        # noinspection PyUnboundLocalVariable
        cl.set_input_settings(textItem["sourceName"], settings, True)

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
    if "sampwidth" not in configData:
        wavTempFile = io.BytesIO(convert_to_wav_bytes(ttsVoice.generate_audio_bytes("test")))
        wf = wave.open(wavTempFile, "rb")
        configData["sampwidth"] = wf.getsampwidth()
        configData["channels"] = wf.getnchannels()
        configData["framerate"] = wf.getframerate()
        json.dump(configData, open("config.json", "w"),indent=4)

    outputStream = pyAudio.open(format=pyAudio.get_format_from_width(configData["sampwidth"]), channels=configData["channels"], rate=configData["framerate"], output=True, output_device_index=chosenOutput)
    print("\nListening for voice input...\n")
    while micStream.is_active():
        data = micStream.read(4096, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            recognizedText = recognizer.Result()[14:-3]
            if recognizedText != "":
                print("Recognized text: " + recognizedText)
                if recasePuncEnable:
                    print("Running recasepunc...")
                    # noinspection PyUnboundLocalVariable
                    tokens = list(enumerate(predictor.tokenize(recognizedText)))
                    results = ""
                    for token, case_label, punc_label in predictor.predict(tokens, lambda x: x[1]):
                        prediction = predictor.map_punc_label(predictor.map_case_label(token[1], case_label), punc_label)
                        if token[1][0] == '\'' or (len(results) > 0 and results[-1] == '\''):
                            results = results + prediction
                        elif token[1][0] != '#':
                            results = results + ' ' + prediction
                        else:
                            results = results + prediction
                    print("Recognized text after recasepunc:")
                    print(results.strip())
                    recognizedText = results
                wavTempFile = io.BytesIO(convert_to_wav_bytes(ttsVoice.generate_audio_bytes(recognizedText)))
                if wavTempFile is not None:
                    if subtitleEnable:
                        print("Setting OBS text...")
                        wrappedLines = textwrap.wrap(recognizedText, 45)
                        wrappedText = ""
                        for line in wrappedLines:
                            wrappedText += line + "\n"
                        wrappedText = wrappedText[:len(wrappedText) - 1]
                        if not recasePuncEnable:    #Only do this if we're not already running recasepunc.
                            wrappedText = wrappedText[0].upper() + wrappedText[1:] + "."
                        print("Wrapped text: " + wrappedText)
                        settings = {"text": wrappedText}
                        # noinspection PyUnboundLocalVariable
                        cl.set_input_settings(textItem["sourceName"], settings, True)
                    print("Playing back audio...")
                    outputStream.write(wavTempFile.read())
                    print("\nListening for voice input...\n")
def convert_to_wav_bytes(mp3Bytes:bytes) -> bytes:
    wavBytes = io.BytesIO()
    sound = AudioSegment.from_file_using_temporary_files(io.BytesIO(mp3Bytes), format="mp3")
    sound.export(wavBytes, format="wav")
    wavBytes.seek(0)
    return wavBytes.read()

def setup():
    # Setup
    defaultConfig: dict[str, str | int] = {
        "api_key": "",
        "vosk_model_path": "",
        "repunc_model_path": "",
        "obs_password": "",
        "obs_port": 4455
    }

    if not os.path.exists("config.json"):
        json.dump(defaultConfig, open("config.json", "w"), indent=4)

    global configData
    try:
        configData = json.load(open("config.json", "r"))
    except:
        print("Invalid config! Did you remember to escape the backslashes?")
        exit()

    if configData["api_key"] == "":
        configData["api_key"] = input("Please input your elevenlabs API key. It can be found on the site, under profile.")
        json.dump(configData, open("config.json", "w"))

    if yesNo("Would you like to edit the settings for OBS websocket?"):
        configData["obs_password"] = input("Please input the password.")
        configData["obs_port"] = input("Please input the port.")
        json.dump(configData, open("config.json","w"))

    voskModelPath = ""
    if configData["vosk_model_path"] != "":
        voskModelPath = configData["vosk_model_path"]
    else:
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
            i = 0
            for directory in eligibleDirectories:
                print(str(i+1) + ") " + directory)
                i += 1
            chosenDirIndex = getNumber("Found multiple eligible vosk models. Please choose one.", minValue=1, maxValue=len(eligibleDirectories))-1
            voskModelPath = eligibleDirectories[chosenDirIndex]

    global voskModel
    voskModel = Model(voskModelPath)

    user = ElevenLabsUser(configData["api_key"])

    voiceList = user.get_available_voices()

    print("Voices available:")
    for voice in voiceList:
        print(str(voiceList.index(voice) + 1) + ") " + voice.initialName + " (" + voice.voiceID + ")")
    chosenVoiceIndex = -1
    while not (0 <= chosenVoiceIndex < len(voiceList)):
        try:
            chosenVoiceIndex = int(input("Please choose a number.\n")) - 1
        except:
            print("Not a valid number.")

    global ttsVoice
    ttsVoice = voiceList[chosenVoiceIndex]



if __name__ == '__main__':
    setup()
    main()
