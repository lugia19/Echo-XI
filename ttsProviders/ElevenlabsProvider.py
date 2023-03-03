import io
import wave

from elevenlabslib import ElevenLabsUser
from pydub import AudioSegment

import helper
from helper import updateConfigFile
from ttsProviders.__TTSProviderAbstract import TTSProvider

class ElevenlabsProvider(TTSProvider):
    def __init__(self):
        eDefaultConfigData = {
            "api_key":"",
            "voice_id":""
        }
        if self.__class__.__name__ not in helper.configData["ttsConfig"]:
            helper.configData["ttsConfig"][self.__class__.__name__] = eDefaultConfigData

        eConfigData = helper.configData["ttsConfig"][self.__class__.__name__]
        for key in eDefaultConfigData:
            if key not in eConfigData:
                eConfigData[key] = ""
                updateConfigFile()

        if eConfigData["api_key"] == "":
            eConfigData["api_key"] = input("Please input your elevenlabs API key. It can be found on the site, under profile.")
            updateConfigFile()

        user = ElevenLabsUser(eConfigData["api_key"])
        voiceList = user.get_available_voices()

        print("Voices available:")
        for voice in voiceList:
            print(str(voiceList.index(voice) + 1) + ") " + voice.initialName + " (" + voice.voiceID + ")")
        chosenVoiceIndex = -1
        while not (0 <= chosenVoiceIndex < len(voiceList)):
            try:
                chosenVoiceIndex = int(input("Please choose a number.\n")) - 1
            except:
                print("Not a valid number.")

        self.ttsVoice = voiceList[chosenVoiceIndex]
    def synthesizeAndPlayAudio(self, prompt, outputDeviceIndex) -> None:
        self.ttsVoice.generate_and_stream_audio(prompt, outputDeviceIndex)