import textwrap
import helper
import obsws_python as obs

textItem:dict
wsClient:obs.ReqClient
def subtitle_setup(hostAddress, obsPort, obsPassword):
    obsPort = obsPort
    global wsClient
    wsClient = obs.ReqClient(host=hostAddress, port=obsPort, password=obsPassword)
    currentScene = wsClient.get_current_program_scene().current_program_scene_name
    print(currentScene)
    itemList = wsClient.get_scene_item_list(currentScene).scene_items

    global textItem
    for item in itemList:
        if item["inputKind"] == "text_gdiplus_v2":
            if helper.choose_yes_no("Found text item " + item["sourceName"] + ", use it for subtitles?"):
                textItem = item
                break
    if textItem is None:
        input("No text item found or selected in current scene. Press enter to exit...")
        return
    settings = {"text": ""}
    # Clean whatever text was there before
    # noinspection PyUnboundLocalVariable
    wsClient.set_input_settings(textItem["sourceName"], settings, True)

def subtitle_update(subtitleText:str):
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