import os

import pyttsx3
import sounddevice as sd
import soundfile as sf
import helper
from ttsProviders.__TTSProviderAbstract import TTSProvider

class PyttsxProvider(TTSProvider):
    def __init__(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        voiceNames = list()
        for voice in voices:
            voiceNames.append(voice.name)

        chosenVoice = voiceNames.index(helper.chooseFromListOfStrings("Please choose a voice.",voiceNames))
        chosenVoice = voices[chosenVoice].id
        self.engine.setProperty("voice",chosenVoice)
    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        self.engine.save_to_file(prompt,"temp.wav")
        self.engine.runAndWait()
        data, fs = sf.read('temp.wav')
        sd.play(data, fs, blocking=True)
        os.remove("temp.wav")
        return