import io
import queue
import threading
import wave

import requests.exceptions
from elevenlabslib import ElevenLabsUser

import helper
from helper import update_config_file
from ttsProviders.__TTSProviderAbstract import TTSProvider

class ElevenlabsProvider(TTSProvider):
    def __init__(self):
        self.eventQueue = queue.Queue()
        self.readyForPlaybackEvent = threading.Event()
        self.readyForPlaybackEvent.set()

        configData = helper.get_provider_config(self)

        apiKeyInput = {
            "xi_api_key":
                {
                    "widget_type": "textbox",
                    "label": "Elevenlabs API Key",
                    "hidden": True
                }
        }


        while True:
            user = ElevenLabsUser(helper.ask_fetch_from_and_update_config(apiKeyInput, configData)["xi_api_key"])
            try:
                 voiceList = user.get_available_voices()
                 break
            except requests.exceptions.HTTPError:
                if not helper.choose_yes_no("Error! API Key incorrect or expired. Try again?"):
                    exit()

        voiceStringList = list()
        for voice in voiceList:
            voiceStringList.append(voice.initialName + " (" + voice.voiceID + ")")

        voiceInput = {
            "voice_id": {
                "widget_type": "list",
                "label": "Choose a voice",
                "options": voiceStringList
            }
        }

        voiceID = helper.ask_fetch_from_and_update_config(voiceInput, configData)["voice_id"]
        voiceID = voiceID[voiceID.find("(")+1:voiceID.find(")")]
        self.ttsVoice = user.get_voice_by_ID(voiceID)

        helper.update_provider_config(self, configData)
        threading.Thread(target=self.waitForPlaybackReady).start()


    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        newEvent = threading.Event()
        self.eventQueue.put(newEvent)
        def startcallbackfunc():
            newEvent.wait()
            print("Playing audio: " + prompt)
        def endcallbackfunc():
            print("Finished playing audio:" + prompt)
            self.readyForPlaybackEvent.set()

        self.ttsVoice.generate_and_stream_audio(prompt, outputDeviceIndex,
                                                streamInBackground=True,
                                                onPlaybackStart=startcallbackfunc,
                                                onPlaybackEnd=endcallbackfunc)

    def waitForPlaybackReady(self):
        while True:
            self.readyForPlaybackEvent.wait()
            self.readyForPlaybackEvent.clear()
            nextEvent = self.eventQueue.get()
            nextEvent.set()