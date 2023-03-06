import json
import threading

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
            configData = helper.get_provider_config(self)

            if configData["speech_key"] == "":
                configData["speech_key"] = input("Please input your azure API key.")

            if configData["service_region"] == "":
                configData["service_region"] = input("Please input your service region.")

            helper.update_provider_config(self, configData)



            auto_detect_source_language_config = None
            translation_config = None
            speech_config = None

            languages = ["en-US"]
            useStoredLanguageList = False
            self.multiLingual = False
            #Check if we have a stored language list. If we do, override everything and use that.
            if len(configData["language_list"]) > 0:
                useStoredLanguageList = True
                languages = configData["language_list"]
                if len(configData["language_list"]) > 1:
                    self.multiLingual = True
            else:
                self.multiLingual = helper.choose_yes_no("Are you going to be speaking in a language other than english?"
                                                "\nYou can choose up to 10 different languages that will be recognized.")


            if self.multiLingual:
                endpoint_string = "wss://{}.stt.speech.microsoft.com/speech/universal/v2".format(configData["service_region"])

                translation_config = speechsdk.translation.SpeechTranslationConfig(
                    subscription=configData["speech_key"],
                    endpoint=endpoint_string,
                    speech_recognition_language='en-US',
                    target_languages=['en'])

                translation_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode, value='Continuous')
                translation_config.set_profanity(profanity_option=speechsdk.ProfanityOption(2))  # Disable the profanity filter.

                if not useStoredLanguageList:
                    languages = []
                    if helper.choose_yes_no("Would you like to view the list of supported languages in your browser?"):
                        import webbrowser
                        webbrowser.open("https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt", new=2, autoraise=True)
                    print("Note: Please do not include the same language multiple times with the same locale (ex: don't include both en-US and en-GB)")

                    while len(languages) <= 10:
                        print("Your currently selected languages are: " + str(languages))
                        if len(languages) > 0 and not helper.choose_yes_no("Would you like to add another language?"):
                            break

                        print("Please input the language in the BCP-47 format (ex: en-US).")
                        newLang = input("Please input the language code.")
                        if newLang not in languages:
                            languages.append(newLang)
                    if helper.choose_yes_no("Would you like to always use this list of languages?"):
                        configData["language_list"] = languages
                        helper.update_provider_config(self, configData)
                auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(languages=languages)

            self.selectedLanguage = None
            #If the user chose "no" at the prompt or if they only selected one language.
            if len(languages) == 1:
                self.multiLingual = False
                self.selectedLanguage = languages[0]
                speech_config = speechsdk.SpeechConfig(subscription=configData["speech_key"], region=configData["service_region"])
                speech_config.speech_recognition_language = self.selectedLanguage
                speech_config.set_profanity(profanity_option=speechsdk.ProfanityOption(2)) #Disable the profanity filter
            try:
                inputDevice = self.chooseInputDevice()
                audio_config = speechsdk.AudioConfig(False, device_name=inputDevice)
            except NotImplementedError:
                audio_config = speechsdk.AudioConfig()


            self.recognizer: speechsdk.translation.TranslationRecognizer|speechsdk.SpeechRecognizer
            if self.multiLingual:
                self.recognizer = speechsdk.translation.TranslationRecognizer(
                                                                            translation_config=translation_config,
                                                                            audio_config=audio_config,
                                                                            auto_detect_source_language_config=auto_detect_source_language_config)
            else:
                self.recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    @staticmethod
    def chooseInputDevice() -> str:
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

            chosenDevice = helper.choose_from_list_of_strings("Please select an input device.", deviceNames)
            chosenDevice = chosenDevice[chosenDevice.find(" - ID: ")+len(" - ID: "):]
            return chosenDevice
        elif platform.system() == "Linux":
            #Luckily portaudio includes the ALSA device IDs as part of the device name.
            inputInfo = helper.select_portaudio_device("input")
            #HDA Intel PCH: HDMI 6 (hw:0,12)
            inputName = inputInfo["name"]
            nameStart = inputName.find("(hw:")
            nameEnd = inputName.find(")",nameStart)+1
            alsaName = inputName[nameStart:nameEnd]
            print("Alsa device name: " + alsaName)
            return alsaName

    def recognize_loop(self):
        try:
            #self.recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
            self.recognizer.recognized.connect(self.text_recognized)
            self.recognizer.session_stopped.connect(self.stop_rec)
            self.recognizer.canceled.connect(self.stop_rec)
            self.recognizer.start_continuous_recognition()
            self.recognitionEndEvent.wait()
        except KeyboardInterrupt:
            self.stop_rec("keyboard interrupt")
            print("Stopping...")

    def text_recognized(self, evt):
        print("Recognized text:" + evt.result.text)
        from speechToSpeech import process_text
        if self.multiLingual:
            resultJson = json.loads(evt.result.json)
            if resultJson["SpeechPhrase"]["RecognitionStatus"] != "Success":
                return
            recognizedText = resultJson["SpeechPhrase"]["DisplayText"]
            recognizedLanguage = resultJson["SpeechPhrase"]["PrimaryLanguage"]["Language"]
            process_text(recognizedText, recognizedLanguage)
        else:
            process_text(evt.result.text, self.selectedLanguage)

    def stop_rec(self,evt):
        print('CLOSING on {}'.format(evt))
        self.recognitionEndEvent.set()
