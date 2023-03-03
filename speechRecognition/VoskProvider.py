import os
from typing import Optional
import pyaudio

from vosk import Model, KaldiRecognizer

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider

class VoskProvider(SpeechRecProvider):
    def __init__(self):
        super().__init__()
        self.type = "vosk"
        self.model = Model(self.select_model_from_dir())
        self.recognizer:Optional[KaldiRecognizer] = None
        self.inputRate = -1
        self.micID = -1
    def setup_recognition(self, microphoneData):
        self.inputRate = int(microphoneData["defaultSampleRate"])
        self.recognizer:KaldiRecognizer = KaldiRecognizer(self.model, self.inputRate)
        self.micID = microphoneData["index"]

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
            print("Could not automatically determine location of vosk model, please either put it in the same directory as the script or set the location in config.json")
            exit()
        elif len(eligibleDirectories) == 1:
            voskModelPath = eligibleDirectories[0]
        else:
            voskModelPath = helper.chooseFromListOfStrings("Found multiple eligible vosk models. Please choose one.", eligibleDirectories)
        return voskModelPath
    def recognize_loop(self):
        pyABackend = pyaudio.PyAudio()
        micStream = pyABackend.open(format=pyaudio.paInt16, channels=1, rate=self.inputRate, input=True, frames_per_buffer=8192, input_device_index=self.micID)
        try:
            while micStream.is_active():
                data = micStream.read(4096, exception_on_overflow=False)

                if self.recognizer.AcceptWaveform(data):
                    recognizedText = self.recognizer.Result()[14:-3]
                    if recognizedText != "":
                        print("Recognized text: " + recognizedText)
                        from speechToSpeech import process_text
                        process_text(recognizedText)
                        print("\nListening for voice input...\n")
        except KeyboardInterrupt:
            exit("Interrupted by user.")
