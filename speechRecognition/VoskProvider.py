import datetime
import os
import zipfile
from typing import Optional
import platform

#if platform.system() == "Windows":
#    import pyaudiowpatch as pyaudio
#else:
#    import pyaudio

import pyaudio
from misc.recasepuncCaller import *


from vosk import Model, KaldiRecognizer

import helper
from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider

voskModelLinks = {
    'vosk-model-en-us-0.22': 'https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip',
    "vosk-model-small-en-us-0.15":"https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
    'vosk-model-cn-0.22': 'https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip',
    'vosk-model-ru-0.42': 'https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip',
    'vosk-model-fr-0.22': 'https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip',
    'vosk-model-de-0.21': 'https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip',
    'vosk-model-es-0.42': 'https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip',
    'vosk-model-it-0.22': 'https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip',
    'vosk-model-ja-0.22': 'https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip'
}

class VoskProvider(SpeechRecProvider):
    def __init__(self):
        super().__init__()
        self.type = "vosk"
        self.recognitionStartedTime = None
        voskConfig = helper.get_provider_config(self)

        voskInputs = dict()
        defaultDevice = pyaudio.PyAudio().get_default_input_device_info()
        defaultDevice = f"{defaultDevice['name']} - {defaultDevice['index']}"
        inputDeviceInput = {
            "widget_type": "list",
            "options": helper.get_list_of_portaudio_devices("input"),
            "label": "Audio input device",
            "default_value": defaultDevice
        }

        availableVoskDirs = self.list_downloaded_models()


        dirNames = list()
        for directory in availableVoskDirs:
            dirName = directory[directory.rfind("\\")+1:]
            dirNames.append(dirName)

        linkNames = list()
        for linkName in voskModelLinks.keys():
            if linkName not in dirNames:
                linkNames.append(linkName + " (download)")

        jointList = list()
        jointList.extend(dirNames)
        jointList.extend(linkNames)

        voskModelPathInput = {
            "widget_type": "list",
            "options": jointList,
            "label": "Choose which vosk model to use"
        }

        voskLanguageInput = {
            "widget_type": "textbox",
            "label": "Language you will be speaking"
        }

        voskInputs["input_device"] = inputDeviceInput
        voskInputs["model_path"] = voskModelPathInput
        voskInputs["language"] = voskLanguageInput

        if helper.choose_yes_no("You must specify the language you will be speaking as a two letter ISO_639-1 code."
                                "\nWould you like to open the list of ISO_639-1 codes in your browser?", enableRemember=True):
            import webbrowser
            webbrowser.open("https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes", new=2, autoraise=True)
        userInputs = helper.ask_fetch_from_and_update_config(voskInputs, voskConfig, "Vosk settings")


        if voskConfig["model_path"] in dirNames:
            voskModelPath = availableVoskDirs[dirNames.index(voskConfig["model_path"])]
        else:
            modelName = voskConfig["model_path"].replace(" (download)","")
            link = voskModelLinks[modelName]
            downloadPath = os.path.join("models", "vosk", modelName + ".zip")
            helper.show_text("Download will start once you press OK...")
            helper.download_file_with_progress(link, downloadPath)
            with zipfile.ZipFile(downloadPath, 'r') as zip_ref:
                zip_ref.extractall(os.path.join("models", "vosk"))  #All the vosk models already contain a folder named correctly
            voskModelPath = downloadPath[:downloadPath.rfind(".zip")]
            os.remove(downloadPath)

        self.model = Model(voskModelPath)

        self.chosenLanguage = userInputs["language"]
        self.recasepuncEnabled = recasepunc_setup(languageCode=self.chosenLanguage)

        self.microphoneInfo = helper.get_portaudio_device_info_from_name(voskConfig["input_device"])
        self.recognizer:KaldiRecognizer = KaldiRecognizer(self.model, self.microphoneInfo["defaultSampleRate"])

    @staticmethod
    def list_downloaded_models() -> list[str]:
        voskModelsDir = os.path.join("models", "vosk")
        print("Looking for available vosk models in " +voskModelsDir+"...")
        eligibleDirectories = list()
        for directory in os.listdir(voskModelsDir):
            if os.path.isdir(os.path.join(voskModelsDir, directory)) and "vosk-model-" in directory:
                eligibleDirectories.append(os.path.join(voskModelsDir, directory))

        return eligibleDirectories

    def recognize_loop(self):
        pyABackend = pyaudio.PyAudio()
        micStream = pyABackend.open(
                                    format=pyaudio.paInt16,
                                    channels=1, #The number of channels MUST be 1 for vosk to work.
                                    rate=int(self.microphoneInfo["defaultSampleRate"]),
                                    input=True,
                                    frames_per_buffer=8192,
                                    input_device_index=self.microphoneInfo["index"]
                                    )
        try:
            while micStream.is_active():
                data = micStream.read(4096, exception_on_overflow=False)
                if self.recognizer.AcceptWaveform(data):
                    if self.recognitionStartedTime is None:  # Is this a good way to measure latency? I'm not sure.
                        self.recognitionStartedTime = datetime.datetime.now()
                    recognizedText = self.recognizer.Result()[14:-3]
                    recognizedTime = datetime.datetime.now()
                    if recognizedText != "" and recognizedText != "the":
                        #Why filter out "the"? Because vosk has a weird tendency to recognize silence as "the" and nobody is going to literally just say "The" and nothing else, come on.
                        if self.recasepuncEnabled:
                            recognizedText = recasepunc_parse(recognizedText)
                        print("\nRecognized text: " + recognizedText)
                        print(f"Time taken to recognize text: {(recognizedTime - self.recognitionStartedTime).total_seconds()}s")

                        from speechToSpeech import process_text
                        process_text(recognizedText, self.chosenLanguage, self.recognitionStartedTime, recognizedTime)
                    self.recognitionStartedTime = None
        except KeyboardInterrupt:
            exit("Interrupted by user.")
