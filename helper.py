import json
import os
import platform
from typing import Mapping


#if platform.system() == "Windows":
#    import pyaudiowpatch as pyaudio
#else:
#    import pyaudio

import pyaudio

from speechRecognition.__SpeechRecProviderAbstract import SpeechRecProvider
from ttsProviders.__TTSProviderAbstract import TTSProvider

ttsProvider:TTSProvider
subtitlesEnabled = False
chosenOutput = -1


defaultConfig: dict[str, str | int| list|float] = {
        "is_post_refactoring" : True,
        "obs_settings": {
            "obs_password": "",
            "obs_port": 4455,
            "obs_host": "localhost"
        },
        "deepl_settings": {
            "api_key":""
        },
        "text_to_speech_config": {
            "ElevenlabsProvider": {
                "api_key": "",
                "voice_id": ""
            }
        },
        "speech_recognition_config":{
            "VoskProvider": {
                "model_path": "",
                "repunc_model_path": ""
            },
            "WhisperProvider": {
                "api_key":"",
                "pause_time": 0.8,
                "energy_threshold": 250,
                "dynamic_energy_threshold": True
            },
            "AzureProvider": {
                "speech_key" : "",
                "service_region": "",
                "language_list": []
            }
        }
}

_configData:dict = {}

def choose_yes_no(prompt: str, trueOption: str = "Yes", falseOption: str = "No") -> bool:
    print(prompt)
    while True:
        userInput = input(trueOption + " or " + falseOption + "?")
        if (trueOption.lower().find(userInput.lower()) == 0) ^ (falseOption.lower().find(userInput.lower()) == 0):
            return trueOption.lower().find(userInput.lower()) == 0

def choose_int(prompt, minValue, maxValue) -> int:
    print(prompt)
    chosenVoiceIndex = -1
    while not (minValue <= chosenVoiceIndex <= maxValue):
        try:
            chosenVoiceIndex = int(input("Input a number between " + str(minValue) +" and " + str(maxValue)+"\n"))
        except:
            print("Not a valid number.")
    return chosenVoiceIndex

def choose_float(prompt, minValue, maxValue) -> int:
    print(prompt)
    chosenVoiceIndex = -1
    while not (minValue <= chosenVoiceIndex <= maxValue):
        try:
            chosenVoiceIndex = float(input("Input a number between " + str(minValue) +" and " + str(maxValue)+"\n"))
        except:
            print("Not a valid number.")
    return chosenVoiceIndex

def choose_from_list_of_strings(prompt, options:list[str]) -> str:
    print(prompt)
    if len(options) == 1:
        print("Choosing the only available option: " + options[0])
        return options[0]

    for index, option in enumerate(options):
        print(str(index+1) + ") " + option)

    chosenOption = choose_int("", 1, len(options)) - 1
    return options[chosenOption]


def update_config_file():
    json.dump(_configData, open("config.json", "w"), indent=4)

def setup_config():
    global defaultConfig

    if not os.path.exists("config.json"):
        json.dump(defaultConfig, open("config.json", "w"), indent=4)

    global _configData
    try:
        _configData = json.load(open("config.json", "r"))
    except:
        print("Invalid config! Did you remember to escape the backslashes?")
        exit()

    if "is_post_refactoring" not in _configData:
        input("The format of config.json is outdated, it will be deleted and remade.\nCopy anything you need to from it then press enter.")
        _configData = defaultConfig
        json.dump(defaultConfig, open("config.json", "w"), indent=4)

    for key, value in defaultConfig.items():
        if key not in _configData:
            _configData[key] = value


    while choose_yes_no("Would you like to edit any of your settings?"):
        _edit_config_property_recursive(_configData)

    print("")

def _edit_config_property_recursive(dictToChooseFrom:dict):
    options = list()
    for key, value in dictToChooseFrom.items():
        if key != "is_post_refactoring":
            options.append(key[0].upper() + key[1:].replace("_", " "))
    chosenOption = choose_from_list_of_strings("Which one would you like to edit?", options)
    if chosenOption not in dictToChooseFrom:
        chosenKey = (chosenOption[0].lower() + chosenOption[1:]).replace(" ", "_")
    else:
        chosenKey = chosenOption
    chosenProperty = dictToChooseFrom[chosenKey]

    if type(chosenProperty) == str:
        dictToChooseFrom[chosenKey] = input("Please input the new value for " + chosenOption + " (current value:" +chosenProperty+")")
        update_config_file()
    elif type(chosenProperty) == list:
        while True:
            chosenProperty = dictToChooseFrom[chosenKey]
            print("The current value of " + chosenOption + " is " + str(chosenProperty))
            if len(chosenProperty) == 0:
                addOrRemove = True
            else:
                addOrRemove = choose_yes_no("Would you like to add or remove an item from the list?", trueOption="Add", falseOption="Remove")
            if addOrRemove:
                dictToChooseFrom[chosenKey].append(input("Please input the new item."))
            else:
                dictToChooseFrom[chosenKey].remove(choose_from_list_of_strings("Please choose which item to remove.",chosenProperty))
            if not choose_yes_no("Would you like to continue editing the list?"):
                break
        update_config_file()
    elif type(chosenProperty) == dict:
        _edit_config_property_recursive(chosenProperty)

def get_provider_config(provider: SpeechRecProvider | TTSProvider) -> dict[str, str|float|bool|int|list]:

    if type(provider) == TTSProvider:
        providerType = "text_to_speech_config"
    else:
        providerType = "speech_recognition_config"

    if providerType not in _configData:
        _configData[providerType] = dict()

    className = provider.__class__.__name__
    if className not in _configData[providerType]:
        _configData[providerType][className] = dict()

    return _configData[providerType][className]

def update_provider_config(provider: SpeechRecProvider | TTSProvider, providerConfig:dict):
    if type(provider) == TTSProvider:
        providerType = "text_to_speech_config"
    else:
        providerType = "speech_recognition_config"

    className = provider.__class__.__name__

    _configData[providerType][className] = providerConfig
    update_config_file()

def get_obs_config():
    return _configData["obs_settings"]

def get_deepl_config():
    return _configData["deepl_settings"]
def select_portaudio_device(deviceType:str, alsaOnly=False):
    """
    Makes the user choose an input or output device and returns that device's info.
    """
    if deviceType != "output" and deviceType != "input":
        raise ValueError("Invalid audio device type.")
    pyABackend = pyaudio.PyAudio()
    hostAPIinfo = None
    if platform.system() == "Windows":
        for i in range(pyABackend.get_host_api_count()):
            apiInfo = pyABackend.get_host_api_info_by_index(i)
            if "WASAPI" in apiInfo["name"]:
                hostAPIinfo = apiInfo
                break
    elif platform.system() == "Linux":
        for i in range(pyABackend.get_host_api_count()):
            apiInfo = pyABackend.get_host_api_info_by_index(i)
            if "ALSA" in apiInfo["name"]:
                hostAPIinfo = apiInfo
                break
    if hostAPIinfo is None:
        hostAPIinfo = pyABackend.get_default_host_api_info()

    deviceNames = list()

    for i in range(hostAPIinfo["deviceCount"]):
        device = pyABackend.get_device_info_by_host_api_device_index(hostAPIinfo["index"], i)
        if device["max" + deviceType[0].upper() + deviceType[1:] + "Channels"] > 0:
            if platform.system() == "Linux" and alsaOnly:
                if "(hw:" in device["name"]:
                    deviceNames.append(device["name"] + " - " + str(device["index"]))
            else:
                deviceNames.append(device["name"] + " - " + str(device["index"]))

    chosenDeviceID = choose_from_list_of_strings("Please choose your " + deviceType + " device.", deviceNames)
    chosenDeviceID = int(chosenDeviceID[chosenDeviceID.rfind(" - ") + 3:])
    chosenDeviceInfo = pyABackend.get_device_info_by_index(chosenDeviceID)
    print("\nChosen "+deviceType+" info: " + str(chosenDeviceInfo) + "\n")
    return chosenDeviceInfo