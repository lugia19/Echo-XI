import datetime
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
                },
            "stability":
                {
                    "widget_type": "textbox",
                    "label": "Stability (Between 0% and 100%, lower is more expressive)",
                    "value_type": "int",
                    "min_value": 0,
                    "max_value": 100
                },
            "clarity":
                {
                    "widget_type": "textbox",
                    "label": "Clarity+similarity boost (Between 0% and 100%, higher is clearer)",
                    "value_type": "int",
                    "min_value": 0,
                    "max_value": 100
                }
        }

        userData = helper.ask_fetch_from_and_update_config(apiKeyInput, configData,"Elevenlabs settings")
        while True:
            user = ElevenLabsUser(userData["xi_api_key"])
            try:
                 voiceList = user.get_available_voices()
                 break
            except requests.exceptions.HTTPError:
                if not helper.choose_yes_no("Error! API Key incorrect or expired. Try again?"):
                    exit()
                userData = helper.ask_fetch_from_and_update_config(apiKeyInput, configData, "Elevenlabs settings")

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

        voiceID = helper.ask_fetch_from_and_update_config(voiceInput, configData,"Elevenlabs voice picker")["voice_id"]
        voiceID = voiceID[voiceID.find("(")+1:voiceID.find(")")]
        self.ttsVoice = user.get_voice_by_ID(voiceID)
        self.ttsVoice.edit_settings(stability=userData["stability"]/100, similarity_boost=userData["clarity"]/100)
        threading.Thread(target=self.waitForPlaybackReady).start()


    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex, startTime, recognizedTime) -> None:
        newEvent = threading.Event()
        self.eventQueue.put(newEvent)
        def startcallbackfunc():
            print(f"Time taken from zero to playback ready: {(datetime.datetime.now() - startTime).total_seconds()}s")
            print(f"Time taken from text recognized to playback ready: {(datetime.datetime.now() - recognizedTime).total_seconds()}s")
            newEvent.wait()
            print("Playing audio: " + prompt)
            if helper.subtitlesEnabled:
                from misc.obsSubtitles import subtitle_update
                subtitle_update(prompt)
        def endcallbackfunc():
            print("Finished playing audio:" + prompt)
            self.readyForPlaybackEvent.set()

        streamEnabled = True
        if streamEnabled:
            self.ttsVoice.generate_and_stream_audio(prompt=prompt, portaudioDeviceID=outputDeviceIndex,
                                                    streamInBackground=True,
                                                    onPlaybackStart=startcallbackfunc,
                                                    onPlaybackEnd=endcallbackfunc)
        else:
            kwargs = {
                "prompt": prompt,
                "portaudioDeviceID": outputDeviceIndex,
                "playInBackground": True,
                "onPlaybackStart": startcallbackfunc,
                "onPlaybackEnd": endcallbackfunc
            }
            threading.Thread(target=self.ttsVoice.generate_and_play_audio,kwargs=kwargs).start()




    def waitForPlaybackReady(self):
        while True:
            self.readyForPlaybackEvent.wait()
            self.readyForPlaybackEvent.clear()
            nextEvent = self.eventQueue.get()
            nextEvent.set()