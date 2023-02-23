import os

import pyttsx3

import helper
from ttsProviders.__TTSProviderAbstract import TTSProvider

engine: pyttsx3.Engine
class PyttsxProvider(TTSProvider):
    def __init__(self):
        global engine
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        voiceNames = list()
        for voice in voices:
            voiceNames.append(voice.name)

        chosenVoice = voiceNames.index(helper.chooseFromListOfStrings("Please choose a voice.",voiceNames))
        chosenVoice = voices[chosenVoice].id
        engine.setProperty("voice",chosenVoice)
    def synthesizeToWavBytes(self, prompt) -> bytes:
        engine.save_to_file(prompt,"temp.wav")
        engine.runAndWait()
        fp = open("temp.wav","rb")
        fileBytes = fp.read()
        fp.close()
        os.remove("temp.wav")
        return fileBytes