import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
import azure.cognitiveservices.speech as speechsdk
import os
import time
class AzureProvider(SpeechRecProvider):
    def __init__(self):
        raise NotImplementedError()

        super().__init__()
        defaultConfig = {
            "speech_key" : "",
            "service_region": ""
        }
        if "srConfig" not in helper.configData:
            helper.configData["srConfig"] = dict()

        if self.__class__.__name__ not in helper.configData["srConfig"]:
            helper.configData["ttsConfig"][self.__class__.__name__] = defaultConfig

        configData = helper.configData["ttsConfig"][self.__class__.__name__]
        for key in defaultConfig:
            if key not in configData:
                configData[key] = ""
                helper.updateConfigFile()

        if configData["speech_key"] == "":
            configData["speech_key"] = input("Please input your azure API key.")
            helper.updateConfigFile()

        if configData["service_region"] == "":
            configData["service_region"] = input("Please input your service region.")
            helper.updateConfigFile()
        self.speech_config = speechsdk.SpeechConfig(subscription=configData["speech_key"], region=configData["service_region"])
        self.speech_recognizer:speechsdk.SpeechRecognizer = None
        self.type = "azure"

    def setup_recognition(self, microphoneData):

        pass

    def recognize_loop(self):
        try:
            pass
        except KeyboardInterrupt:
            self.speech_recognizer
            print("Stopping...")

