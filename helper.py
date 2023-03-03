import json
import os

from ttsProviders.__TTSProviderAbstract import TTSProvider

ttsProvider:TTSProvider
subtitlesEnabled = False
chosenOutput = -1

defaultConfig: dict[str, str | int] = {
        "api_key": "",
        "vosk_model_path": "",
        "repunc_model_path": "",
        "obs_password": "",
        "obs_port": 4455,
        "obs_host": "localhost",
        "ttsConfig": {}
}

configData:dict = {}

def yesNo(prompt) -> bool:
    print(prompt)
    userInput = ""
    while len(userInput) == 0 or (userInput[0].lower() != "y" and userInput[0].lower() != "n"):
        userInput = input("y/n?")
    return userInput[0].lower() == "y"

def getNumber(prompt, minValue, maxValue) -> int:
    print(prompt)
    chosenVoiceIndex = -1
    while not (minValue <= chosenVoiceIndex <= maxValue):
        try:
            chosenVoiceIndex = int(input("Input a number between " + str(minValue) +" and " + str(maxValue)+"\n"))
        except:
            print("Not a valid number.")
    return chosenVoiceIndex

def chooseFromListOfStrings(prompt, options:list[str]) -> str:
    print(prompt)
    if len(options) == 1:
        print("Choosing the only available option: " + options[0])
        return options[0]

    for index, option in enumerate(options):
        print(str(index+1) + ") " + option)

    chosenOption = getNumber("", 1, len(options))-1
    return options[chosenOption]


def updateConfigFile():
    json.dump(configData, open("config.json", "w"), indent=4)

def setupConfig():
    global defaultConfig

    if not os.path.exists("config.json"):
        json.dump(defaultConfig, open("config.json", "w"), indent=4)

    global configData
    try:
        configData = json.load(open("config.json", "r"))
    except:
        print("Invalid config! Did you remember to escape the backslashes?")
        exit()

    for key, value in defaultConfig.items():
        if key not in configData:
            configData[key] = value

    if yesNo("Would you like to edit the settings for the OBS websocket integration?"):
        configData["obs_password"] = input("Please input the password.")
        configData["obs_port"] = input("Please input the port.")
        if yesNo("Is the server going to be on another computer?"):
            configData["obs_host"] = input("Please input the IP address of the other computer (without the port)")
        else:
            configData["obs_host"] = "localhost"
        updateConfigFile()