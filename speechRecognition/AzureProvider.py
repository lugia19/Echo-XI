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

        speech_config = speechsdk.SpeechConfig(subscription=configData["speech_key"], region=configData["service_region"])
        if helper.choose_yes_no("Are you going to be speaking a language other than English?"):
            print("Please input the language in the BCP-47 format (ex: en-US).")
            if helper.choose_yes_no("Would you like to view the language list in your browser?"):
                import webbrowser
                webbrowser.open("https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/language-support?tabs=stt", new=2, autoraise=True)
            speech_config.speech_recognition_language = input("Please input your language.")
        else:
            speech_config.speech_recognition_language = "en-US"
        speech_config.set_profanity(profanity_option=speechsdk.ProfanityOption(2)) #Disable the profanity filter


        try:
            inputDevice = self.chooseInputDevice()
            audio_config = speechsdk.AudioConfig(False, device_name=inputDevice)
        except NotImplementedError:
            audio_config = speechsdk.AudioConfig()

        self.speech_recognizer:speechsdk.SpeechRecognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    @staticmethod
    def chooseInputDevice() -> str:
        # I haven't figured out how to iterate ALSA device IDs on linux, because I'm not using it on my main computer, so we default to the default input device.
        # Feel free to make a PR to add this if you know how to.
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
        else:
            print("I don't use linux/macOS on my main system so I haven't figured out how to select an input device on those platforms for azure.")
            print("Sticking with the default input device.")
            raise NotImplementedError("")

    def recognize_loop(self):
        try:
            self.speech_recognizer.recognizing.connect(lambda evt: print('RECOGNIZING: {}'.format(evt)))
            self.speech_recognizer.recognized.connect(self.text_recognized)
            self.speech_recognizer.session_stopped.connect(self.stop_rec)
            self.speech_recognizer.canceled.connect(self.stop_rec)
            self.speech_recognizer.start_continuous_recognition()
            self.recognitionEndEvent.wait()
        except KeyboardInterrupt:
            self.stop_rec("keyboard interrupt")
            print("Stopping...")

    @staticmethod
    def text_recognized(evt):
        print(evt)
        from speechToSpeech import process_text
        process_text(evt.result.text)

    def stop_rec(self,evt):
        print('CLOSING on {}'.format(evt))
        self.recognitionEndEvent.set()
