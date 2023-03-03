import io
import os
import numpy
import pyaudio
import soundfile

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
import whisper
class WhisperProvider(SpeechRecProvider):
    def __init__(self):
        raise NotImplementedError()

        super().__init__()
        self.type = "whisper"
        modelOptions = ["Base (1GB)","Small (2GB)","Medium (5GB)", "Large (10GB)"]
        chosenModel = helper.chooseFromListOfStrings("Here are the available whisper models alongside their VRAM requirements. Please choose one.", modelOptions)
        if "Large" not in chosenModel:
            self.useMultiLingual = helper.yesNo("Are you going to be speaking languages other than english?")
        else:
            self.useMultiLingual = True
        modelBaseName = chosenModel[:chosenModel.find(" ")].lower()
        print("Chosen model name: " + modelBaseName + ("" if self.useMultiLingual else ".en"))
        self.model = whisper.load_model(modelBaseName + ("" if self.useMultiLingual else ".en"))
        self.sampleRate = -1
    def setup_recognition(self, microphoneData):
        self.sampleRate = microphoneData["defaultSampleRate"]

    def recognize_loop(self) -> str:
        array = numpy.frombuffer(chosenInput, dtype="int16")
        soundfile.write("temp.wav", array, int(self.sampleRate))

        audio = whisper.load_audio("temp.wav", self.sampleRate)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        if self.useMultiLingual:
            _, probs = self.model.detect_language(mel)
            print(f"Detected language: {max(probs, key=probs.get)}")
            language = max(probs, key=probs.get)
        else:
            language = "en"

        if language == "en":
            result = whisper.transcribe(self.model, audio)
        else:
            options = whisper.DecodingOptions(task="translate")
            result = whisper.decode(self.model, mel, options)

        os.remove("temp.wav")
        return result["text"]