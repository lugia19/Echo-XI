import os
import queue
import threading

import sounddevice as sd
import soundfile as sf
import pyttsx3
import helper
import tempfile
from ttsProviders.__TTSProviderAbstract import TTSProvider

class PyttsxProvider(TTSProvider):
    def __init__(self):
        self.engine = pyttsx3.init()
        self.eventQueue = queue.Queue()
        self.playbackReadyEvent = threading.Event()
        self.playbackReadyEvent.set()
        voices = self.engine.getProperty('voices')
        voiceNames = list()
        configData = helper.get_provider_config(self)
        for voice in voices:
            voiceNames.append(voice.name)

        pyttsx3Inputs = {
            "voice_name": {
                "widget_type": "list",
                "options": voiceNames,
                "label": "Choose a voice"
            }
        }

        userInputs = helper.ask_fetch_from_and_update_config(pyttsx3Inputs, configData,"Pyttsx3 voice picker")

        chosenVoice = voiceNames.index(userInputs["voice_name"])
        chosenVoice = voices[chosenVoice].id
        self.engine.setProperty("voice",chosenVoice)
        threading.Thread(target=self.waitForEvent).start()

    def synthesizeAndWaitForEvent(self, prompt, outputDeviceIndex, event:threading.Event):
        temp = tempfile.NamedTemporaryFile(suffix=".wav", mode="wb+", delete=False)
        fileName = temp.name
        self.engine.save_to_file(prompt, fileName)
        temp.close()
        self.engine.runAndWait()
        soundFile = sf.SoundFile(fileName)
        event.wait()

        sd.play(soundFile.read(), samplerate=soundFile.samplerate, blocking=True, device=outputDeviceIndex)
        soundFile.close()
        os.remove(fileName)
        self.playbackReadyEvent.set()

    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        newEvent = threading.Event()
        threading.Thread(target=self.synthesizeAndWaitForEvent, args=(prompt,outputDeviceIndex,newEvent)).start()
        self.eventQueue.put(newEvent)
    def waitForEvent(self):
        while True:
            self.playbackReadyEvent.wait()
            self.playbackReadyEvent.clear()
            newEvent = self.eventQueue.get()
            newEvent.set()
