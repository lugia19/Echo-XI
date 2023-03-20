import os
from misc.recasepunc import CasePuncPredictor, WordpieceTokenizer
import helper
predictor:CasePuncPredictor
def recasepunc_setup(languageCode:str) -> bool:
    # This variable only exists to make pycharm figure out that the import is used.
    uselessVar: WordpieceTokenizer


    recasePuncInputs = dict()

    eligibleDirectoriesAndfiles = list_recasepunc_models()
    while len(eligibleDirectoriesAndfiles) == 0:
        if helper.choose_yes_no("Could not find any recasepunc models in " + os.path.join(os.getcwd(), "models", "recasepunc") +
                                "\nWould you like to open the two download pages for recasepunc models in your browser?"):
            import webbrowser
            webbrowser.open("https://alphacephei.com/vosk/models", new=2, autoraise=True)
            webbrowser.open("https://github.com/benob/recasepunc", new=2, autoraise=True)
        if not helper.choose_yes_no("Would you like to try again?"):
            return False
        eligibleDirectoriesAndfiles = list_recasepunc_models()


    dirOrFileNames = list()
    for dirOrFile in eligibleDirectoriesAndfiles:
        dirOrFileNames.append(dirOrFile[dirOrFile.rfind("\\")+1:])

    recasePuncModelInput = {
        "widget_type": "list",
        "label": "Recasepunc model",
        "options": dirOrFileNames
    }

    recasePuncEnabledInput = {
        "widget_type": "checkbox",
        "label": "Enable recasepunc"
    }

    recasePuncInputs["model_path"] = recasePuncModelInput
    recasePuncInputs["enabled"] = recasePuncEnabledInput

    configData = helper.get_recasepunc_config()

    userInputs = helper.ask_fetch_from_and_update_config(recasePuncInputs, configData)

    if not userInputs["enabled"]:
        return False #Exit immediately

    recasePuncDirOrFile = os.path.join("models", "recasepunc", userInputs["model_path"])
    repuncModelPath = ""
    if os.path.isdir(recasePuncDirOrFile):
        filesInDir = os.listdir(recasePuncDirOrFile)
        if "checkpoint" in filesInDir:
            repuncModelPath = os.path.join(recasePuncDirOrFile, "checkpoint")
        else:
            if len(filesInDir) == 1:
                repuncModelPath = os.path.join(recasePuncDirOrFile, filesInDir[0])
            else:
                chooseFileInput = {
                    "model_file": {
                        "widget_type": "list",
                        "options": filesInDir,
                        "label": "Please select which file is the actual mode."
                    }
                }
                chosenFile = helper.ask_fetch_from_and_update_config(chooseFileInput, configData)["model_file"]
                repuncModelPath = os.path.join(recasePuncDirOrFile, chosenFile)

    global predictor
    from misc.recasepunc import default_flavors
    if languageCode in default_flavors.keys():
        flavor = default_flavors[languageCode]
    else:
        flavor = None
    predictor = CasePuncPredictor(repuncModelPath, lang=languageCode, flavor=flavor)

    return True
def list_recasepunc_models() -> list[str]:
    modelsDir = os.path.join("models", "recasepunc")
    eligibleDirectoriesAndfiles = list()
    if not os.path.exists("models"):
        os.mkdir("models")
    if not os.path.exists(modelsDir):
        os.mkdir(modelsDir)
    for directory in os.listdir(modelsDir):
        eligibleDirectoriesAndfiles.append(os.path.join(modelsDir, directory))

    if len(eligibleDirectoriesAndfiles) == 0:
        if helper.choose_yes_no("Could not automatically determine location of recasepunc model, please put it in " + modelsDir +
                                "\nWould you like to open the two download pages for recasepunc models in your browser?"):
            import webbrowser
            webbrowser.open("https://alphacephei.com/vosk/models", new=2, autoraise=True)
            webbrowser.open("https://github.com/benob/recasepunc", new=2, autoraise=True)
        exit()
    return eligibleDirectoriesAndfiles

def recasepunc_parse(textToParse:str) -> str:
    print("Running recasepunc...")
    # noinspection PyUnboundLocalVariable
    tokens = list(enumerate(predictor.tokenize(textToParse)))
    results = ""
    for token, case_label, punc_label in predictor.predict(tokens, lambda x: x[1]):
        prediction = predictor.map_punc_label(predictor.map_case_label(token[1], case_label), punc_label)
        if token[1][0] == '\'' or (len(results) > 0 and results[-1] == '\''):
            results = results + prediction
        elif token[1][0] != '#':
            results = results + ' ' + prediction
        else:
            results = results + prediction
    print("Recognized text after recasepunc:")
    print(results.strip())
    return results