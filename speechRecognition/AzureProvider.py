from __future__ import annotations

import datetime
import json
import threading

import requests

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
import azure.cognitiveservices.speech as speechsdk
import platform

if platform.system() == "Windows":
    import comtypes
    from pycaw.pycaw import AudioUtilities, IMMDeviceEnumerator, EDataFlow, DEVICE_STATE
    from pycaw.constants import CLSID_MMDeviceEnumerator
class AzureProvider(SpeechRecProvider):
    def __init__(self):
            super().__init__()
            self.type = "azure"
            self.recognitionEndEvent = threading.Event()
            self.recognitionStartedTime = None
            configData = helper.get_provider_config(self)

            azureConfigInputs = dict()
            speechKeyInput = {
                "widget_type": "textbox",
                "label": "Azure API Key",
                "hidden": True
            }
            serviceRegionInput = {
                "widget_type": "textbox",
                "label": "Azure Service Region"
            }

            azureConfigInputs["azure_speech_key"] = speechKeyInput
            azureConfigInputs["service_region"] = serviceRegionInput


            try:
                deviceNames = self.list_input_devices()
                inputDeviceInput = {
                    "widget_type": "list",
                    "label": "Audio Input Device",
                    "options": deviceNames
                }

                azureConfigInputs["input_device"] = inputDeviceInput
            except NotImplementedError:
                audio_config = speechsdk.AudioConfig()


            multilingualInput = {
                "widget_type": "checkbox",
                "label": "Use languages other than English?",
                "description": "You can choose up to 10 different languages that will be recognized by inputting their BCP-47 code (ex: en-US)."
                               "\nNOTE: Do not include two locales for the same language (ex: en-US and en-GB)."
            }
            azureConfigInputs["multilingual"] = multilingualInput

            while True:
                result = helper.ask_fetch_from_and_update_config(azureConfigInputs, configData, "Azure configuration")
                testUrl = f"https://{configData['service_region']}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
                headers = {
                    "Ocp-Apim-Subscription-Key": result["azure_speech_key"]
                }
                response = requests.post(testUrl, headers=headers)
                if response.ok:
                    break
                else:
                    if not helper.choose_yes_no("Error! Incorrect or expired API Key. Try again?"):
                        exit()

            if "input_device" in result:
                deviceName = result["input_device"]
                audio_config = speechsdk.AudioConfig(False, device_name=self.get_device_id_from_name(deviceName))





            auto_detect_source_language_config = None
            translation_config = None
            speech_config = None
            languages = ["en-US"]

            self.multiLingual = result["multilingual"]


            if self.multiLingual:
                endpoint_string = "wss://{}.stt.speech.microsoft.com/speech/universal/v2".format(result["service_region"])

                translation_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=result["azure_speech_key"],
                    endpoint=endpoint_string,
                    speech_recognition_language='en-US',    #Unused value
                    target_languages=['en'])                #Also unused


                translation_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode, value='Continuous')
                translation_config.set_profanity(profanity_option=speechsdk.ProfanityOption(2))  # Disable the profanity filter.

                azureTranslationInputs = {
                    "language_list": {
                        "widget_type": "textbox",
                        "label" : "Please input UP TO 10 languages in BCP-47 format separated by commas (ex: 'en-US, it-IT')"
                    }
                }

                if helper.choose_yes_no("Would you like to view the list of supported languages in your browser?", enableRemember=True):
                    import webbrowser
                    webbrowser.open("https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt", new=2, autoraise=True)
                userInput = helper.ask_fetch_from_and_update_config(azureTranslationInputs, configData,"Azure multilanguage settings")

                languages = [x.strip() for x in userInput["language_list"].split(",")]
                if len(languages) > 10:
                    languages = languages[:10]  # Discard anything over 10 languages.

                auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=languages)

            self.selectedLanguage = None
            #If the user chose "no" at the prompt or if they only selected one language.
            if len(languages) == 1:
                self.multiLingual = False
                self.selectedLanguage = languages[0]
                speech_config = speechsdk.SpeechConfig(subscription=result["azure_speech_key"], region=result["service_region"])
                speech_config.speech_recognition_language = self.selectedLanguage
                speech_config.set_profanity(profanity_option=speechsdk.ProfanityOption(2)) #Disable the profanity filter again.


            self.recognizer: speechsdk.translation.TranslationRecognizer|speechsdk.SpeechRecognizer
            if self.multiLingual:
                self.recognizer = speechsdk.translation.TranslationRecognizer(
                                                                            translation_config=translation_config,
                                                                            audio_config=audio_config,
                                                                            auto_detect_source_language_config=auto_detect_source_language_config)
            else:
                self.recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    @staticmethod
    def list_input_devices() -> list[str]:
        if platform.system() == "Windows":
            #Code to enumerate input devices adapted from https://github.com/AndreMiras/pycaw/issues/50#issuecomment-981069603
            devices = list()
            deviceEnumerator = comtypes.CoCreateInstance(
                CLSID_MMDeviceEnumerator,
                IMMDeviceEnumerator,
                comtypes.CLSCTX_INPROC_SERVER)
            if deviceEnumerator is None:
                raise ValueError("Couldn't find any devices.")

            collection = deviceEnumerator.EnumAudioEndpoints(EDataFlow.eCapture.value, DEVICE_STATE.ACTIVE.value)
            if collection is None:
                raise ValueError("Couldn't find any devices.")

            count = collection.GetCount()
            for i in range(count):
                dev = collection.Item(i)
                if dev is not None:
                    if not ": None" in str(AudioUtilities.CreateDevice(dev)):
                        devices.append(AudioUtilities.CreateDevice(dev))

            deviceNames = list()
            for device in devices:
                deviceNames.append(device.FriendlyName + " - ID: "+device.id)

            return deviceNames
        elif platform.system() == "Linux":
            #Luckily portaudio includes the ALSA device IDs as part of the device name.
            return helper.get_list_of_portaudio_devices("input", alsaOnly=True)
        else:
            raise NotImplementedError()

    @staticmethod
    def get_device_id_from_name(deviceName:str) -> str:
        if platform.system() == "Windows":
            deviceID = deviceName[deviceName.find(" - ID: ")+len(" - ID: "):]
            return deviceID
        elif platform.system() == "Linux":
            nameStart = deviceName.find("(hw:")
            nameEnd = deviceName.find(")", nameStart) + 1
            alsaName = deviceName[nameStart:nameEnd]
            print("Alsa device name: " + alsaName)
            return alsaName

    def recognize_loop(self):
        try:
            self.recognizer.recognizing.connect(self.set_recognition_start_time)
            self.recognizer.recognized.connect(self.text_recognized)
            self.recognizer.session_stopped.connect(self.stop_rec)
            self.recognizer.canceled.connect(self.stop_rec)
            self.recognizer.start_continuous_recognition()
            self.recognitionEndEvent.wait()
        except KeyboardInterrupt:
            self.recognizer.stop_continuous_recognition()
            self.stop_rec("keyboard interrupt")
            print("Stopping...")

    def set_recognition_start_time(self, evt):
        if self.recognitionStartedTime is None:
            self.recognitionStartedTime = datetime.datetime.now()

    def text_recognized(self, evt):
        print("\nRecognized text:" + evt.result.text)
        recognizedTime = datetime.datetime.now()
        print(f"Time taken to recognize text: {(recognizedTime-self.recognitionStartedTime).total_seconds()}s")

        from speechToSpeech import process_text
        if self.multiLingual:
            resultJson = json.loads(evt.result.json)
            if resultJson["SpeechPhrase"]["RecognitionStatus"] != "Success":
                return
            recognizedText = resultJson["SpeechPhrase"]["DisplayText"]
            recognizedLanguage = resultJson["SpeechPhrase"]["PrimaryLanguage"]["Language"]
            process_text(recognizedText, recognizedLanguage, self.recognitionStartedTime, recognizedTime)
        else:
            process_text(evt.result.text, self.selectedLanguage, self.recognitionStartedTime, recognizedTime)

        self.recognitionStartedTime = None
    def stop_rec(self,evt):
        print('CLOSING on {}'.format(evt))
        self.recognitionEndEvent.set()
