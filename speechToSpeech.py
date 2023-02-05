from __future__ import annotations

import io
import json
import os
import textwrap
import wave
from typing import Optional
import pyaudio
import requests
from pydub import AudioSegment
from vosk import Model, KaldiRecognizer

# If you don't want the OBS integration, you can remove this import
import obsws_python as obs
# If you don't want the recasepunc functionality, you can remove this imports
from recasepunc import CasePuncPredictor

#Setup
if not os.path.exists("config.json"):
    configData:dict[str, str|int] = {
        "api_key": "API_KEY",
        "vosk_model_path": "VOSK_MODEL_PATH",
        "voice_ID": "VOICE_ID",
        "repunc_model_path":"REPUNC_MODEL_PATH_(OPTIONAL)"
    }
    json.dump(configData, open("config.json", "w"), indent=4)
    print("Please fill in the settings in config.json!")
    exit()

try:
    configData = json.load(open("config.json", "r"))
except:
    print("Invalid config! Did you remember to escape the backslashes?")
    exit()

modelPath = configData["vosk_model_path"]
voiceID = configData["voice_ID"]
api_key = configData["api_key"]

ttsURL = "https://api.elevenlabs.io/v1/text-to-speech/" + configData["voice_ID"] + "/stream"
ttsHeader = {
    'accept': '*/*',
    'Content-Type': 'application/json',
    "xi-api-key": configData["api_key"],
}

def main():
    try:
        model = Model(modelPath)
    except:
        print("Could not open model. Did you remember to double escape the backslashes in the config?")
        exit()

    print("Enable text output for OBS websocket?")
    userInput = ""
    while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
        userInput=input("y/n?")
    subtitleEnable = userInput[0].lower() == "y"

    print("Would you like to enable case/punctuation detection? (Improves AI voice and subtitles)")
    userInput = ""
    while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
        userInput = input("y/n?")
    recasePuncEnable = userInput[0].lower() == "y"
    if recasePuncEnable:
        if configData["repunc_model_path"] == "REPUNC_MODEL_PATH_(OPTIONAL)":
            print("Please set the repunc_model_path in the config file!")
            exit()
        predictor = CasePuncPredictor(configData["repunc_model_path"], lang="en", flavor="bert-base-uncased")

    if subtitleEnable:
        userInput = ""
        if "obsPassword" in configData:
            cl = obs.ReqClient(host="localhost", port=4455, password=configData["obsPassword"])
        else:
            print("Are you using a password for websocket?")
            while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
                userInput = input("y/n?")
            if userInput[0].lower() == "y":
                cl = obs.ReqClient(host="localhost",port=4455,password=input("Please input your password."))
            else:
                cl = obs.ReqClient(host="localhost", port=4455, password="")
        currentScene = cl.get_current_program_scene().current_program_scene_name
        print(currentScene)
        itemList = cl.get_scene_item_list(currentScene).scene_items
        textItem = None
        for item in itemList:
            if item["inputKind"] == "text_gdiplus_v2":
                print("Found text item " + item["sourceName"] + ", use it for subtitles?")
                userInput = ""
                while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
                    userInput = input("y/n?")
                if userInput == "y":
                    textItem = item
                    break
        if textItem is None:
            input("No text item found or selected in current scene. Press enter to exit...")
            exit()

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
    recognizer = KaldiRecognizer(model, inputRate)

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
        wavTempFile = getWavBytesIOFromText("test")
        wf = wave.open(wavTempFile, "rb")
        configData["sampwidth"] = wf.getsampwidth()
        configData["channels"] = wf.getnchannels()
        configData["framerate"] = wf.getframerate()
        json.dump(configData, open("config.json", "w"),indent=4)

    outputStream = pyAudio.open(format=pyAudio.get_format_from_width(configData["sampwidth"]), channels=configData["channels"], rate=configData["framerate"], output=True, output_device_index=chosenOutput)

    print("\nNow listening for voice input...\n")
    while micStream.is_active():
        data = micStream.read(4096, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            recognizedText = recognizer.Result()[14:-3]
            if recognizedText != "":
                print("Recognized text: " + recognizedText)
                if recasePuncEnable:
                    print("Running recasepunc...")
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

                wavTempFile = getWavBytesIOFromText(recognizedText)
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
                        cl.set_input_settings(textItem["sourceName"], settings, True)
                    print("Playing back audio...")
                    outputStream.write(wavTempFile.read())





def getWavBytesIOFromText(prompt:str) -> Optional[io.BytesIO]:
    payload = {"text":prompt}
    response = requests.post(ttsURL, headers=ttsHeader, json=payload)
    if response.status_code == 200:
        print("Response received correctly.")
        wavBytes = io.BytesIO()
        sound = AudioSegment.from_file_using_temporary_files(io.BytesIO(response.content), format="mp3")
        sound.export(wavBytes, format="wav")
        wavBytes.seek(0)
        return wavBytes
    else:
        return None

if __name__ == '__main__':
    main()
