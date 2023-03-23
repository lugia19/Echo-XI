import datetime
import os
from typing import Optional
import platform

#if platform.system() == "Windows":
#    import pyaudiowpatch as pyaudio
#else:
#    import pyaudio

import pyaudio
from misc.recasepuncCaller import *


from vosk import Model, KaldiRecognizer

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider

class VoskProvider(SpeechRecProvider):
    def __init__(self):
        super().__init__()
        self.type = "vosk"
        self.recognitionStartedTime = None
        voskConfig = helper.get_provider_config(self)

        voskInputs = dict()
        inputDeviceInput = {
            "widget_type": "list",
            "options": helper.get_list_of_portaudio_devices("input"),
            "label": "Choose your input device"
        }

        availableVoskDirs = self.list_models()

        while len(availableVoskDirs) == 0:
            if helper.choose_yes_no("Could not automatically determine location of vosk model, please put it in " + os.path.join(os.getcwd(),"models","vosk") +
                                    "\nWould you like to open the download page for vosk models in your browser?"):
                import webbrowser
                webbrowser.open("https://alphacephei.com/vosk/models", new=2, autoraise=True)
            if not helper.choose_yes_no("Would you like to try again?"):
                exit()
            availableVoskDirs = self.list_models()

        dirNames = list()

        for directory in availableVoskDirs:
            dirNames.append(directory[directory.rfind("\\")+1:])

        voskModelPathInput = {
            "widget_type": "list",
            "options": dirNames,
            "label": "Choose which vosk model to use"
        }

        voskLanguageInput = {
            "widget_type": "textbox",
            "label": "Language you will be speaking"
        }

        voskInputs["input_device"] = inputDeviceInput
        voskInputs["model_path"] = voskModelPathInput
        voskInputs["language"] = voskLanguageInput

        if helper.choose_yes_no("You must specify the language you will be speaking as a two letter ISO_639-1 code."
                                "\nWould you like to open the list of ISO_639-1 codes in your browser?"):
            import webbrowser
            webbrowser.open("https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes", new=2, autoraise=True)
        userInputs = helper.ask_fetch_from_and_update_config(voskInputs, voskConfig, "Vosk settings")

        voskModelPath = os.path.join(os.getcwd(),"models","vosk",voskConfig["model_path"])

        self.model = Model(voskModelPath)

        self.chosenLanguage = userInputs["language"]
        self.recasepuncEnabled = recasepunc_setup(languageCode=self.chosenLanguage)

        self.microphoneInfo = helper.get_portaudio_device_info_from_name(voskConfig["input_device"])
        self.recognizer:KaldiRecognizer = KaldiRecognizer(self.model, self.microphoneInfo["defaultSampleRate"])

    @staticmethod
    def list_models() -> list[str]:
        voskModelsDir = os.path.join(os.getcwd(), "models", "vosk")
        print("Looking for available vosk models in " +voskModelsDir+"...")
        eligibleDirectories = list()
        for directory in os.listdir(voskModelsDir):
            if os.path.isdir(os.path.join(voskModelsDir, directory)) and "vosk-model-" in directory:
                eligibleDirectories.append(os.path.join(voskModelsDir, directory))

        return eligibleDirectories

    def recognize_loop(self):
        pyABackend = pyaudio.PyAudio()
        micStream = pyABackend.open(
                                    format=pyaudio.paInt16,
                                    channels=1, #The number of channels MUST be 1 for vosk to work.
                                    rate=int(self.microphoneInfo["defaultSampleRate"]),
                                    input=True,
                                    frames_per_buffer=8192,
                                    input_device_index=self.microphoneInfo["index"]
                                    )
        try:
            while micStream.is_active():
                data = micStream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    if self.recognitionStartedTime is None:  # Is this a good way to measure latency? I'm not sure.
                        self.recognitionStartedTime = datetime.datetime.now()
                    recognizedText = self.recognizer.Result()[14:-3]
                    recognizedTime = datetime.datetime.now()
                    if recognizedText != "":
                        if self.recasepuncEnabled:
                            recognizedText = recasepunc_parse(recognizedText)
                        print("\nRecognized text: " + recognizedText)
                        print(f"Time taken to recognize text: {(recognizedTime - self.recognitionStartedTime).total_seconds()}s")

                        from speechToSpeech import process_text
                        process_text(recognizedText, self.chosenLanguage, self.recognitionStartedTime, recognizedTime)
                    self.recognitionStartedTime = None
        except KeyboardInterrupt:
            exit("Interrupted by user.")
