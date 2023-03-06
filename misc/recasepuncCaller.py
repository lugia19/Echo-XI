import os
from misc.recasepunc import CasePuncPredictor, WordpieceTokenizer
import helper
predictor:CasePuncPredictor
def recasepunc_setup(languageCode, overrideRepuncModelPath=None):
    repuncModelPath = ""

    #This variable only exists to make pycharm figure out that the import is used.
    uselessVar:WordpieceTokenizer

    if overrideRepuncModelPath is None or overrideRepuncModelPath == "":
        modelsDir = os.path.join("models", "recasepunc")
        print("Recase model path not set in config, checking if there is one in " + modelsDir + "...")
        eligibleDirectoriesAndfiles = list()

        if not os.path.exists("models"):
            os.mkdir("models")

        if not os.path.exists(modelsDir):
            os.mkdir(modelsDir)

        for directory in os.listdir(modelsDir):
            eligibleDirectoriesAndfiles.append(os.path.join(modelsDir,directory))

        if len(eligibleDirectoriesAndfiles) == 0:
            print("Could not automatically determine location of recasepunc model, please either put it in the same directory as the script or set the location in config.json")
            if helper.choose_yes_no("Would you like to open the two download pages for recasepunc models in your browser?"):
                import webbrowser
                webbrowser.open("https://alphacephei.com/vosk/models", new=2, autoraise=True)
                webbrowser.open("https://github.com/benob/recasepunc", new=2, autoraise=True)
            exit()
        elif len(eligibleDirectoriesAndfiles) == 1:
            repuncModelPath = eligibleDirectoriesAndfiles[0]
        else:
            options = []
            for dirOrFile in eligibleDirectoriesAndfiles:
                options.append(dirOrFile[dirOrFile.rfind("\\")+1:])

            chosenOption = helper.choose_from_list_of_strings("Found multiple eligible repunc models.", options)
            repuncModelPath = eligibleDirectoriesAndfiles[options.index(chosenOption)]

        if os.path.isdir(repuncModelPath):
            filesInDir = os.listdir(repuncModelPath)
            if "checkpoint" in filesInDir:
                repuncModelPath = os.path.join(repuncModelPath, "checkpoint")
            else:
                if len(filesInDir) == 1:
                    repuncModelPath = os.path.join(repuncModelPath, filesInDir[0])
                else:
                    print("Could not automatically determine which file in this directory is the model.")
                    chosenFile = helper.choose_from_list_of_strings("Please select one.",filesInDir)
                    repuncModelPath = os.path.join(repuncModelPath, chosenFile)

    else:
        repuncModelPath = overrideRepuncModelPath

    global predictor

    print("Found a model. Initializing CasePuncPredictor...")

    from misc.recasepunc import default_flavors
    if languageCode in default_flavors.keys():
        flavor = default_flavors[languageCode]
    else:
        flavor = None
    predictor = CasePuncPredictor(repuncModelPath, lang=languageCode, flavor=flavor)

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