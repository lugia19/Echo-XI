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
        vosk_config = helper.get_provider_config(self)
        if vosk_config["model_path"] != "":
            self.model = Model(vosk_config["model_path"])
        else:
            self.model = Model(self.select_model_from_dir())

        self.recasepuncEnabled = helper.choose_yes_no("Would you like to enable case/punctuation detection? (Improves AI voice and subtitles)")

        if self.recasepuncEnabled:
            print("What language will you be speaking? Please input it as a two letter ISO_639-1 code.")
            if helper.choose_yes_no("Would you like to open the list of ISO_639-1 codes in your browser?"):
                import webbrowser
                webbrowser.open("https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes", new=2, autoraise=True)
            self.chosenLanguage = input("Please input the language code.")

            if vosk_config["repunc_model_path"] != "":
                recasepunc_setup(self.chosenLanguage, vosk_config["repunc_model_path"])
            else:
                print("Note: Please make sure to select a vosk and recasepunc with the SAME LANGUAGE. Otherwise the results will be unpredictable.")
                recasepunc_setup(self.chosenLanguage)

        self.microphoneInfo = helper.select_portaudio_device("input")
        self.recognizer:KaldiRecognizer = KaldiRecognizer(self.model, self.microphoneInfo["defaultSampleRate"])

    @staticmethod
    def select_model_from_dir() -> str:
        voskModelsDir = os.path.join(os.getcwd(), "models", "vosk")
        voskModelPath = None
        print("Looking for available vosk models in " +voskModelsDir+"...")
        eligibleDirectories = list()
        for directory in os.listdir(voskModelsDir):
            if os.path.isdir(os.path.join(voskModelsDir, directory)) and "vosk-model-" in directory:
                eligibleDirectories.append(os.path.join(voskModelsDir, directory))
        if len(eligibleDirectories) == 0:
            print("Could not automatically determine location of vosk model, please put it in " + voskModelsDir)
            if helper.choose_yes_no("Would you like to open the download page for vosk models in your browser?"):
                import webbrowser
                webbrowser.open("https://alphacephei.com/vosk/models", new=2, autoraise=True)
            exit()
        elif len(eligibleDirectories) == 1:
            voskModelPath = eligibleDirectories[0]
        else:
            dirNames = []
            for directory in eligibleDirectories:
                dirNames.append(directory[directory.rfind("\\")+1:])
            chosenName = helper.choose_from_list_of_strings("Found multiple eligible vosk models. Please choose one.", dirNames)
            voskModelPath = eligibleDirectories[dirNames.index(chosenName)]
        return voskModelPath
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
                    recognizedText = self.recognizer.Result()[14:-3]
                    if recognizedText != "":
                        if self.recasepuncEnabled:
                            recognizedText = recasepunc_parse(recognizedText)
                        print("Recognized text: " + recognizedText)

                        from speechToSpeech import process_text
                        process_text(recognizedText, self.chosenLanguage)
                        print("\nListening for voice input...\n")
        except KeyboardInterrupt:
            exit("Interrupted by user.")
