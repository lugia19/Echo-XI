import os
import queue
import threading

import speech_recognition as sr
import tempfile
import whisper.tokenizer

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
import whisper
class WhisperProvider(SpeechRecProvider):
    #Inspired by this repo https://github.com/mallorbc/whisper_mic/blob/main/mic.py
    def __init__(self):
        super().__init__()
        self.type = "whisper"

        modelOptions = ["Base (1GB)","Small (2GB)","Medium (5GB)", "Large (10GB)"]
        chosenModel = helper.choose_from_list_of_strings("Here are the available whisper models alongside their VRAM requirements. Please choose one.", modelOptions)
        if "Large" not in chosenModel:
            self.useMultiLingual = helper.choose_yes_no("Are you going to be speaking languages other than english?")
        else:
            self.useMultiLingual = True
        modelBaseName = chosenModel[:chosenModel.find(" ")].lower() + ("" if self.useMultiLingual else ".en")
        print("Chosen model name: " + modelBaseName)


        self.model = whisper.load_model(modelBaseName)

        #Choose a mic.
        self.microphoneInfo = helper.select_portaudio_device("input")

        self.srMic = sr.Microphone(device_index=self.microphoneInfo["index"], sample_rate=int(self.microphoneInfo["defaultSampleRate"]))

        self.recognizer = sr.Recognizer()
        configData = helper.get_provider_config(self)

        if helper.choose_yes_no("Would you like to edit the voice detection settings for whisper?"):
            options = ["Pause time (How long in seconds you have to pause before a sentence is considered over)",
                       "Energy threshold (How loud you need to be in order for your voice to be detected)",
                       "Dynamic energy threshold (Whether the energy threshold changes based on the detected background noise)"]
            finishedEditing = False
            while not finishedEditing:
                chosenOption = helper.choose_from_list_of_strings("What setting would you like to edit?", options)
                chosenOption = chosenOption[:chosenOption.index("(")].lower()
                if "pause time" in chosenOption:
                    print("The value is currently " + str(configData["pause_time"]))
                    configData["pause_time"] = helper.choose_float("Enter the new value.", 0, 10)
                elif "dynamic energy threshold" in chosenOption:
                    print("The value is currently " + str(configData["dynamic_energy_threshold"]))
                    configData["dynamic_energy_threshold"] = helper.choose_yes_no("Would you like to enable it (y) or disable it (n)?")
                else:
                    print("The value is currently " + str(configData["energy_threshold"]))
                    configData["energy_threshold"] = helper.choose_int("Enter the new value.", 0, 999)
                finishedEditing = helper.choose_yes_no("Are you finished editing the settings?")
            helper.update_provider_config(self, configData)

        self.languageOverride = ""

        if self.useMultiLingual:
            if helper.choose_yes_no("Would you like to manually choose which language you'll be speaking? (This means you will only be able to use this language)"):
                if helper.choose_yes_no("Would you like to view a list of supported languages?"):
                    print("Supported languages:")
                    print("Two letter code: Language name")
                    for key, value in whisper.tokenizer.LANGUAGES.items():
                        print(key + ": " + value)

                langCodes = whisper.tokenizer.LANGUAGES.keys()
                langNames = whisper.tokenizer.LANGUAGES.values()
                chosenLanguage = ""
                while chosenLanguage == "":
                    chosenLanguage = input("Please specify the language, either by its name or its two letter code (ex: italian or it for italian.)")
                    if chosenLanguage not in langCodes and chosenLanguage not in langNames:
                        print("Language not found! Maybe you spelled it wrong?")
                        chosenLanguage = ""
                self.languageOverride = chosenLanguage

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
                recognizedText = self.resultQueue.get()
                process_text(recognizedText)
        except KeyboardInterrupt:
            print("Interrupted by user.")
            self.interruptEvent.set()
        pass
    def recording_loop(self):
        with self.srMic as source:
            while True:
                if self.interruptEvent.is_set():
                    break
                audio = self.recognizer.listen(source)
                temp = tempfile.NamedTemporaryFile(suffix=".wav", mode="wb+",delete=False)
                temp.write(audio.get_wav_data())
                self.audioQueue.put_nowait(temp)

    def recognition_loop(self):
        while True:
            if self.interruptEvent.is_set():
                break
            audioTempFile = self.audioQueue.get()
            audioFilePath = audioTempFile.name
            audioTempFile.close()
            if self.useMultiLingual:
                if self.languageOverride != "":
                    result = self.model.transcribe(audioFilePath, language=self.languageOverride)
                else:
                    result = self.model.transcribe(audioFilePath)

            else:
                result = self.model.transcribe(audioFilePath, language="en")
            recognizedText = result["text"].strip()
            print("Recognized text: " + recognizedText)
            self.resultQueue.put(recognizedText)

            os.remove(audioFilePath)
