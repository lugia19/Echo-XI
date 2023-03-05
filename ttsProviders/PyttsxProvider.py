import os

import sounddevice as sd
import soundfile as sf
import pyttsx3
import helper
from ttsProviders.__TTSProviderAbstract import TTSProvider

class PyttsxProvider(TTSProvider):
    def __init__(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        voiceNames = list()
        for voice in voices:
            voiceNames.append(voice.name)

        chosenVoice = voiceNames.index(helper.choose_from_list_of_strings("Please choose a voice.", voiceNames))
        chosenVoice = voices[chosenVoice].id
        self.engine.setProperty("voice",chosenVoice)
        self.outputStream = None
        self.currentODIndex = -1
    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        self.engine.save_to_file(prompt, "temp.wav")
        self.engine.runAndWait()
        data, fs = sf.read('temp.wav')
        #pyttsx3 outputs in some weeeird samplerate, so both sounddevice and pyaudio completely fuck up at playing it if I try to choose a specific device.
        #If you've got a fix, shoot me a PR, but otherwise it's not really important as this engine is only really good enough for testing.
        sd.play(data, fs, blocking=True)
        os.remove("temp.wav")
        return