from __future__ import annotations

import json
import os
import platform
from typing import Mapping
import tkinter as tk
from tkinter import ttk

backgroundColor = "#2b2b2b"
buttonBackground = "#424242"
foregroundColor = "white"
useGUI = True

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
        "misc_settings": {
            "output_device":"",
            "speech_provider":"",
            "tts_provider":""
        },
        "obs_settings": {
            "obs_password": "",
            "obs_port": 4455,
            "obs_host": "localhost"
        },
        "recasepunc_settings": {
            "model_path": "",
            "enabled": True,
            "language": ""
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
                "model_path": ""
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
    if useGUI:
        def on_yes_click():
            result[0] = True
            window.destroy()

        def on_no_click():
            result[0] = False
            window.destroy()

        # Initialize window
        window = tk.Tk()
        window.title("Question")
        window.configure(bg="#2b2b2b")
        setup_style(window, backgroundColor, buttonBackground,foregroundColor)
        # Create and set a style
        style = ttk.Style()
        # Create and place the prompt label
        prompt_label = ttk.Label(window, text=prompt, wraplength=300)
        prompt_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        # Create and place the yes button
        yes_button = ttk.Button(window, text=trueOption, command=on_yes_click)
        yes_button.grid(row=1, column=0, padx=10, pady=10)

        # Create and place the no button
        no_button = ttk.Button(window, text=falseOption, command=on_no_click)
        no_button.grid(row=1, column=1, padx=10, pady=10)

        # Center the window
        window.eval('tk::PlaceWindow . center')
        result = [False]
        window.mainloop()
        return result[0]
    else:
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
        except ValueError:
            print("Not a valid number.")
    return chosenVoiceIndex

def choose_float(prompt, minValue, maxValue) -> int:
    print(prompt)
    chosenVoiceIndex = -1
    while not (minValue <= chosenVoiceIndex <= maxValue):
        try:
            chosenVoiceIndex = float(input("Input a number between " + str(minValue) +" and " + str(maxValue)+"\n"))
        except ValueError:
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
    if type(chosenProperty) == dict:
        _edit_config_property_recursive(chosenProperty)
    else:
        if type(chosenProperty) == str:
            dictToChooseFrom[chosenKey] = input("Please input the new value for " + chosenOption + " (current value:" +chosenProperty+")")
        elif type(chosenProperty) == int:
            dictToChooseFrom[chosenKey] = choose_int("Please input the new value for " + chosenOption + " (current value:" +chosenProperty+")", minValue=0, maxValue=999)
        elif type(chosenProperty) == float:
            dictToChooseFrom[chosenKey] = choose_float("Please input the new value for " + chosenOption + " (current value:" +chosenProperty+")", minValue=0, maxValue=999)
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


def get_provider_config(provider: SpeechRecProvider | TTSProvider) -> dict[str, str|float|bool|int|list]:

    if TTSProvider in provider.__class__.__bases__:
        providerType = "text_to_speech_config"
    elif SpeechRecProvider in provider.__class__.__bases__:
        providerType = "speech_recognition_config"
    else:
        raise ValueError("Provider does not inherit from either SpeechRecProvider nor TTSProvider!")

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

def get_recasepunc_config():
    return _configData["recasepunc_settings"]


def get_misc_config():
    return _configData["misc_settings"]

def get_deepl_config():
    return _configData["deepl_settings"]
def get_list_of_portaudio_devices(deviceType:str, alsaOnly=False) -> list[str]:
    """
    Returns a list containing all the names of portaudio devices of the specified type.
    """
    if deviceType != "output" and deviceType != "input":
        raise ValueError("Invalid audio device type.")
    pyABackend = pyaudio.PyAudio()
    hostAPIinfo = None
    #This section of code was useful when I was trying to use WASAPI loopback devices.
    #Right now it's actively harmful as WASAPI is a lot more limited with sample rates, which is why it's commented out.

    #if platform.system() == "Windows":
    #    for i in range(pyABackend.get_host_api_count()):
    #        apiInfo = pyABackend.get_host_api_info_by_index(i)
    #        if "WASAPI" in apiInfo["name"]:
    #            hostAPIinfo = apiInfo
    #            break

    if platform.system() == "Linux":
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

    return deviceNames

def get_portaudio_device_info_from_name(deviceName:str):
    pyABackend = pyaudio.PyAudio()
    chosenDeviceID = int(deviceName[deviceName.rfind(" - ") + 3:])
    chosenDeviceInfo = pyABackend.get_device_info_by_index(chosenDeviceID)
    return chosenDeviceInfo

def setup_style(app, backgroundColor, buttonBackground, foregroundColor):
    app.option_add('*TCombobox*Listbox.foreground', foregroundColor)
    app.option_add('*TCombobox*Listbox.background', buttonBackground)
    style = ttk.Style()
    style.theme_use('clam')

    style.configure('.', background=backgroundColor, foreground=foregroundColor)
    style.configure('TLabel', background=backgroundColor, foreground=foregroundColor)
    style.configure('TFrame', background=backgroundColor)
    style.configure('TCheckbutton', background=backgroundColor, foreground=foregroundColor, fieldbackground=backgroundColor)
    style.configure('TCombobox', selectbackground=backgroundColor, fieldbackground=backgroundColor, background=backgroundColor)
    style.configure('TButton', background=buttonBackground, foreground=foregroundColor, bordercolor=buttonBackground)
    style.configure('TEntry', fieldbackground=backgroundColor, foreground=foregroundColor, insertcolor=foregroundColor, insertwidth=2)
    style.map('TCombobox',
              fieldbackground=[('readonly', backgroundColor)],
              selectbackground=[('readonly', backgroundColor)],
              foreground=[('readonly', foregroundColor)])  # Set a lighter shade of gray for lines

    style.map('TCheckbutton',
              background=[('active', buttonBackground)],  # Custom background color on hover
              foreground=[('active', foregroundColor)])  # Custom foreground (text) color on hover

def ask_fetch_from_and_update_config(inputDict:dict, configData:dict):
    for key, value in inputDict.items():
        if key in configData and configData[key] != "":
            value["default_value"] = configData[key]

    if useGUI:
        userInputs = _ask_ui(inputDict)
    else:
        userInputs = _ask_cli(inputDict)

    for key, value in userInputs.items():
        configData[key] = value

    update_config_file()
    return userInputs

def show_text(message):
    app = tk.Tk()
    app.attributes('-alpha', 0)
    setup_style(app, backgroundColor, buttonBackground, foregroundColor)
    show_custom_messagebox(app, "Info", message)
    app.destroy()
def show_custom_messagebox(app, title, message):
    messagebox_window = tk.Toplevel(app)
    messagebox_window.title(title)
    messagebox_window.configure(bg='#2b2b2b')  # Set the background color to match the dark theme
    messagebox_window.highlightthickness = 0  # Remove the default padding

    message_label = ttk.Label(messagebox_window, text=message, padding=(20, 20))
    message_label.grid(row=0, column=0, columnspan=2)

    ok_button = ttk.Button(messagebox_window, text="OK", width=10, command=messagebox_window.destroy)
    ok_button.grid(row=1, column=0, columnspan=2, pady=(0, 20))

    messagebox_window.transient(app)
    messagebox_window.grab_set()
    app.wait_window(messagebox_window)


def _ask_ui(config):
    def on_confirm():
        result = {}
        for key, value in config.items():
            if value["widget_type"] == "list":
                result[key] = value["var"].get()
            elif value["widget_type"] == "checkbox":
                result[key] = value["var"].get()
            elif value["widget_type"] == "textbox":
                if "value_type" in value:
                    try:
                        rawValue = value["entry"].get()
                        if value["value_type"] == "int" or value["value_type"] == "float":

                            if value["value_type"] == "int":
                                result[key] = int(rawValue)
                            elif value["value_type"] == "float":
                                result[key] = float(rawValue)

                            if "max_value" in value:
                                if not result[key] <= value["max_value"]:
                                    raise ValueError()
                            if "min_value" in value:
                                if not result[key] >= value["min_value"]:
                                    raise ValueError()

                        else:
                            raise NotImplementedError("ERROR! TYPE CHECKING FOR "+value["value_type"]+" NOT IMPLEMENTED!")
                    except ValueError as e:
                        show_custom_messagebox(app, "Error!","Could not convert input " + key + " to " + value["value_type"] + ", please double check that your input is formatted correctly!")
                        raise e
                else:
                    result[key] = value["entry"].get()

        app.destroy()
        return result


    def on_combobox_selection_changed(event, combobox_key):
        selected_index = config[combobox_key]["combobox"].current()
        if "descriptions" in config[combobox_key]:
            config[combobox_key]["description_text"].config(state=tk.NORMAL)
            config[combobox_key]["description_text"].delete(1.0, tk.END)
            config[combobox_key]["description_text"].insert(tk.END, config[combobox_key]["descriptions"][selected_index])
            config[combobox_key]["description_text"].config(state=tk.DISABLED)

    def on_checkbox_clicked(checkbox_key):
        currValue = config[checkbox_key]["var"].get()
        if currValue:
            show_custom_messagebox(app, "Info", config[checkbox_key]["description"])

    app = tk.Tk()
    app.title("Settings")
    setup_style(app, backgroundColor, buttonBackground, foregroundColor)
    # (Place the dark theme configuration code here)

    frame = ttk.Frame(app, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    row = 0
    for key, value in config.items():
        if value["widget_type"] == "list":
            label = ttk.Label(frame, text=value["label"])
            label.grid(row=row, column=0, sticky=tk.W)

            value["var"] = tk.StringVar()
            combobox = ttk.Combobox(frame, width=60, textvariable=value["var"], values=value["options"], state="readonly")
            if "default_value" in value:
                try:
                    default_index = value["options"].index(value["default_value"])
                except ValueError:
                    default_index = 0
            else:
                default_index = 0

            combobox.current(default_index)
            combobox.grid(row=row, column=1, sticky=(tk.W, tk.E))
            value["combobox"] = combobox
            combobox.bind("<<ComboboxSelected>>", lambda event, k=key: on_combobox_selection_changed(event, k))

            if "descriptions" in value:
                description_text = tk.Text(frame, height=15, width=60, wrap=tk.WORD, background='#2b2b2b', foreground='white')
                description_text.grid(row=row + 1, column=1, sticky=(tk.W, tk.E))
                description_text.insert(tk.END, value["descriptions"][default_index])
                description_text.config(state=tk.DISABLED)
                value["description_text"] = description_text
                row += 1

        elif value["widget_type"] == "checkbox":
            value["var"] = tk.BooleanVar()
            checkbutton = ttk.Checkbutton(frame, text=value["label"], variable=value["var"])
            checkbutton.grid(row=row, columnspan=2, sticky=tk.W)
            if "default_value" in value:
                value["var"].set(value["default_value"])
            if "description" in value:
                value["var"].trace("w", lambda *args, k=key: on_checkbox_clicked(k))

        elif value["widget_type"] == "textbox":
            label = ttk.Label(frame, text=value["label"])
            label.grid(row=row, column=0, sticky=tk.W)

            value["entry"] = ttk.Entry(frame, width=40)
            if "hidden" in value and value["hidden"]:
                value["entry"].config(show="*")
            value["entry"].grid(row=row, column=1, sticky=(tk.W, tk.E))
            if "default_value" in value:
                value["entry"].insert(0, value["default_value"])

        row += 1

    confirm_button = ttk.Button(frame, text="Confirm", command=app.quit)
    confirm_button.grid(row=row, columnspan=2, pady=10)

    app.mainloop()

    while True:
        try:
            returnValue = on_confirm()
            break
        except ValueError:
            app.mainloop()
    return returnValue

def _ask_cli(innerConfig):
    innerResult = {}

    for key, value in innerConfig.items():
        print("\n")
        if "default_value" in value:
            print(f"Default value for {value['label']}: {value['default_value']}")
            use_default = choose_yes_no("Use default value?")
            if use_default:
                innerResult[key] = value["default_value"]
                continue

        if value["widget_type"] == "list":
            options = value["options"]
            if "descriptions" in value:
                options = [f"{option} - {desc}" for option, desc in zip(value["options"], value["descriptions"])]
            innerResult[key] = choose_from_list_of_strings(value["label"], options)

        elif value["widget_type"] == "checkbox":
            innerResult[key] = choose_yes_no(value["label"])

        elif value["widget_type"] == "textbox":
            if "value_type" in value:
                if value["value_type"] == "int":
                    choose_float(value["label"], minValue=value["min_value"], maxValue=value["max_value"])
                elif value["value_type"] == "float":
                    choose_int(value["label"], minValue=value["min_value"], maxValue=value["max_value"])
                else:
                    raise NotImplementedError("Type checking for this type is not implemented")
            else:
                innerResult[key] = input(f"{value['label']}: ")

    return innerResult