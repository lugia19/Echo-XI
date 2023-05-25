import datetime
import io
import os
import queue
import threading

import speech_recognition as sr
import whisper.tokenizer
import openai
import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
import whisper
import faster_whisper
class WhisperProvider(SpeechRecProvider):
    #Inspired by this repo https://github.com/mallorbc/whisper_mic/blob/main/mic.py
    def __init__(self):
        super().__init__()
        self.type = "whisper"
        self.recognitionStartedTime = None
        configData = helper.get_provider_config(self)

        sharedInput = dict()
        inputDeviceInput = {
            "widget_type": "list",
            "options": helper.get_list_of_portaudio_devices("input"),
            "label": "Choose your input device"
        }
        runOptions = ["Run the model locally", "Use the paid API"]

        runMode = {
            "widget_type": "list",
            "options": runOptions,
            "label": "Choose which mode you'd like"
        }

        pauseTimeInput = {
            "widget_type": "textbox",
            "label": "Pause time (How long in seconds you have to pause before a sentence is considered over)",
            "value_type":"float",
            "min_value": 0,
            "max_value": 10
        }

        energyThresholdInput = {
            "widget_type": "textbox",
            "label": "Energy threshold (How loud you need to be in order for your voice to be detected)",
            "value_type":"int",
            "min_value": 0,
            "max_value": 999
        }

        dynamicThresholdInput = {
            "widget_type": "checkbox",
            "label": "Dynamic energy threshold (Whether the energy threshold changes based on the detected background noise)"
        }

        sharedInput["input_device"] = inputDeviceInput
        sharedInput["run_mode"] = runMode
        sharedInput["pause_time"] = pauseTimeInput
        sharedInput["energy_threshold"] = energyThresholdInput
        sharedInput["dynamic_energy_threshold"] = dynamicThresholdInput
        userInput = helper.ask_fetch_from_and_update_config(sharedInput, configData, "Shared Whisper settings")

        # Set the mic.
        self.microphoneInfo = helper.get_portaudio_device_info_from_name(userInput["input_device"])
        self.srMic = sr.Microphone(device_index=self.microphoneInfo["index"], sample_rate=int(self.microphoneInfo["defaultSampleRate"]))
        self.recognizer = sr.Recognizer()
        self.languageOverride = ""
        self.runLocal = runOptions.index(userInput["run_mode"]) == 0




        if self.runLocal:
            localInputs = dict()
            modelOptions = ["Base (1GB)", "Small (2GB)", "Medium (5GB)", "Large (10GB)"]
            modelInput = {
                "widget_type" : "list",
                "options": modelOptions,
                "label": "Choose a model size (check the VRAM requirements)"
            }

            multilingualInput = {
                "widget_type": "checkbox",
                "label": "Enable non-english language recognition"
            }

            localInputs["model_size"] = modelInput
            localInputs["multilingual"] = multilingualInput
            userLocalInput = helper.ask_fetch_from_and_update_config(localInputs, configData, "Whisper local settings")

            self.useMultiLingual = userLocalInput["multilingual"]

            chosenModel = userLocalInput["model_size"]



            if self.useMultiLingual:
                multiLingualConfig = dict()
                languageList = list()
                for key, value in whisper.tokenizer.LANGUAGES.items():
                    languageList.append(value + " (" + key + ")")

                languageOverrideInput = {
                    "widget_type": "list",
                    "label": "Manually specify speaking language"
                             "\n(Only used if automatic detection is disabled)",
                    "options":languageList
                }

                automaticDetectionInput = {
                    "widget_type" : "checkbox",
                    "label": "Automatic language detection"
                }

                multiLingualConfig["language_override"] = languageOverrideInput
                multiLingualConfig["automatic_detection"] = automaticDetectionInput
                userLocalInput = helper.ask_fetch_from_and_update_config(multiLingualConfig, configData, "Whisper multilingual config")
                if not userLocalInput["automatic_detection"]:
                    #User wants to override the language detection
                    self.languageOverride = userLocalInput["language_override"]
                    self.languageOverride = self.languageOverride[self.languageOverride.find("(")+1:self.languageOverride.find(")")]
                    print(self.languageOverride)
                    if self.languageOverride == "en":
                        #The user is a bloody idiot and said "no" to only using english but then specified english as a language override.
                        #Let's set the model back to the english-only variant.
                        self.useMultiLingual = False
            else:
                if "Large" in chosenModel:
                    self.languageOverride = "en"


            modelBaseName = chosenModel[:chosenModel.find(" ")].lower()
            if not self.useMultiLingual and "Large" not in chosenModel:
                modelBaseName += ".en"
            self.model = faster_whisper.WhisperModel(modelBaseName, device="cuda", compute_type="float16")

            #self.model = whisper.load_model(modelBaseName)
        else:
            apiKeyInput = {
                "openai_api_key":{
                    "widget_type": "textbox",
                    "hidden": True,
                    "label": "OpenAI API Key"
                }
            }

            while True:
                openai.api_key = helper.ask_fetch_from_and_update_config(apiKeyInput, configData, "Whisper API settings")["openai_api_key"]
                try:
                    openai.Model.list()
                    break
                except openai.error.AuthenticationError:
                    if not helper.choose_yes_no("Error! Incorrect or expired API Key. Try again?"):
                        exit()

        self.recognizer.pause_threshold = configData["pause_time"]
        self.recognizer.energy_threshold = configData["energy_threshold"]
        self.recognizer.dynamic_energy_threshold = configData["dynamic_energy_threshold"]

        self.audioQueue = queue.Queue()
        self.resultQueue = queue.Queue()
        self.interruptEvent = threading.Event()


    def recognize_loop(self):
        recordingThread = threading.Thread(target=self.recording_loop)
        recognitionThread = threading.Thread(target=self.recognition_loop)
        recordingThread.start()
        recognitionThread.start()
        try:
            while True:
                from speechToSpeech import process_text
                result = self.resultQueue.get()
                process_text(result["text"], result["lang"], result["start_time"], result["recognized_time"])
        except KeyboardInterrupt:
            print("Interrupted by user.")
            self.interruptEvent.set()

    def recording_loop(self):
        with self.srMic as source:
            while True:
                if self.interruptEvent.is_set():
                    break
                audio = self.recognizer.listen(source)
                if self.recognitionStartedTime is None:
                    self.recognitionStartedTime = datetime.datetime.now()
                self.audioQueue.put_nowait({
                    "audio_data": audio,
                    "start_time": self.recognitionStartedTime
                })
                self.recognitionStartedTime = None

    def recognition_loop(self):
        while True:
            if self.interruptEvent.is_set():
                break
            audioQueueElement = self.audioQueue.get()
            audio = audioQueueElement["audio_data"]
            audioLanguage = None

            if self.runLocal:
                if self.useMultiLingual:
                    if self.languageOverride != "":
                        audioLanguage = self.languageOverride
                        segments, info = self.model.transcribe(io.BytesIO(audio.get_wav_data()), language=self.languageOverride, beam_size=5)
                    else:
                        segments, info = self.model.transcribe(io.BytesIO(audio.get_wav_data()), beam_size=5)
                        audioLanguage = info.language
                else:
                    segments, info = self.model.transcribe(io.BytesIO(audio.get_wav_data()), language="en")
                    audioLanguage = "en"

                recognizedText = ""
                for segment in segments:
                    recognizedText += " " + segment.text
                recognizedText = recognizedText.strip()

            else:
                #The API doesn't return the detected language. Fuck.
                recognizedText = openai.Audio.transcribe("whisper-1", io.BytesIO(audio.get_wav_data())).text

            print("\nRecognized text: " + recognizedText)
            recognizedTime = datetime.datetime.now()
            print(f"Time taken to recognize text: {(recognizedTime-audioQueueElement['start_time']).total_seconds()}s")
            self.resultQueue.put({
                    "text":recognizedText,
                    "lang":audioLanguage,
                    "start_time": audioQueueElement["start_time"],
                    "recognized_time": recognizedTime
                })