import textwrap
import helper
import obsws_python as obs

textItem:dict
wsClient:obs.ReqClient
def subtitle_setup():
    obsConfig = helper.get_obs_config()

    obsInputs = dict()
    enabledInput = {
        "widget_type" : "checkbox",
        "label": "Enable OBS subtitles",
        "description": "Uses OBS' websocket functionality to synchronize the detected text with a text object in the current scene."
    }

    hostInput = {
        "widget_type": "textbox",
        "label" : "The IP address of the computer running the websocket"
    }

    portInput = {
        "widget_type": "textbox",
        "label" : "The port for the websocket",
        "value_type": "int"
    }

    passwordInput = {
        "widget_type": "textbox",
        "label": "The password for the websocket",
        "hidden": True
    }

    obsInputs["obs_host"] = hostInput
    obsInputs["obs_port"] = portInput
    obsInputs["obs_password"] = passwordInput
    obsInputs["enabled"] = enabledInput

    global wsClient
    while True:
        result = helper.ask_fetch_from_and_update_config(obsInputs, obsConfig, "OBS subtitle integration settings")
        helper.subtitlesEnabled = result["enabled"]

        if not result["enabled"]:
            return

        try:
            wsClient = obs.ReqClient(host=result["obs_host"], port=result["obs_port"], password=result["obs_password"])
            break
        except ConnectionError:
            if not helper.choose_yes_no("Could not connect to the websocket server with the given details. Try again?", trueOption="Try again", falseOption="Give up"):
                return

    textItemList = list()
    while len(textItemList) == 0:
        for scene in wsClient.get_scene_list().scenes:
            itemList = wsClient.get_scene_item_list(scene["sceneName"]).scene_items
            for item in itemList:
                if item["inputKind"] == "text_gdiplus_v2" and item not in textItemList:
                    textItemList.append(item)

        if len(textItemList) == 0:
            if not helper.choose_yes_no("No text items found in any scene. Would you like to try again?"):
                return

    textItemInput = {
        "text_item": {
            "widget_type": "list",
            "options": [item["sourceName"] for item in textItemList],
            "label": "Text item for subtitles"
        }
    }
    chosenTextItemName = helper.ask_fetch_from_and_update_config(textItemInput, obsConfig, "Choose a text object")["text_item"]

    global textItem
    for item in textItemList:
        if item["sourceName"] == chosenTextItemName:
            textItem = item
            break

    settings = {"text": ""}
    # Clean whatever text was there before
    # noinspection PyUnboundLocalVariable
    wsClient.set_input_settings(textItem["sourceName"], settings, True)

def subtitle_update(subtitleText:str):
    currentScene = wsClient.get_current_program_scene().current_program_scene_name
    itemList = wsClient.get_scene_item_list(currentScene).scene_items
    textItemNameList = list()
    for item in itemList:
        if item["inputKind"] == "text_gdiplus_v2" and item not in textItemNameList:
            textItemNameList.append(item["sourceName"])
    if textItem["sourceName"] not in textItemNameList:
        return

    print("Setting OBS text...")
    wrappedLines = textwrap.wrap(subtitleText, 45)
    wrappedText = ""
    for line in wrappedLines:
        wrappedText += line + "\n"
    wrappedText = wrappedText[:len(wrappedText) - 1]
    if wrappedText[0].islower():  # Only do this if we're not already running recasepunc.
        wrappedText = wrappedText[0].upper() + wrappedText[1:] + "."
    print("Wrapped text: " + wrappedText)
    settings = {"text": wrappedText}
    # noinspection PyUnboundLocalVariable
    wsClient.set_input_settings(textItem["sourceName"], settings, True)