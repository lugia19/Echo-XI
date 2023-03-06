import os

import sounddevice as sd
import soundfile as sf
import pyttsx3
import helper
import tempfile
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
    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        temp = tempfile.NamedTemporaryFile(suffix=".wav", mode="wb+", delete=False)
        fileName = temp.name
        self.engine.save_to_file(prompt, fileName)
        temp.close()
        self.engine.runAndWait()
        soundFile = sf.SoundFile(fileName)
        sd.play(soundFile.read(), samplerate=soundFile.samplerate, blocking=False, device=outputDeviceIndex)
        soundFile.close()
        os.remove(fileName)
        return