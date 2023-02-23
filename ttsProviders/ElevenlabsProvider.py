import io
from elevenlabslib import ElevenLabsUser, ElevenLabsVoice
from pydub import AudioSegment

import helper
from helper import updateConfigFile
from ttsProviders.__TTSProviderAbstract import TTSProvider

ttsVoice:ElevenLabsVoice
def convert_to_wav_bytes(mp3Bytes: bytes) -> bytes:
    wavBytes = io.BytesIO()
    sound = AudioSegment.from_file_using_temporary_files(io.BytesIO(mp3Bytes), format="mp3")
    sound.export(wavBytes, format="wav")
    wavBytes.seek(0)
    return wavBytes.read()


class ElevenlabsProvider(TTSProvider):
    def __init__(self):

        eDefaultConfigData = {
            "api_key":"",
            "voice_id":""
        }
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

        global ttsVoice
        ttsVoice = voiceList[chosenVoiceIndex]
    def synthesizeToWavBytes(self, prompt) -> bytes:
        return convert_to_wav_bytes(ttsVoice.generate_audio_bytes(prompt))

