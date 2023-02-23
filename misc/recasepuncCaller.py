import os
from misc.recasepunc import CasePuncPredictor, WordpieceTokenizer
import helper
predictor:CasePuncPredictor
def recasepunc_setup(overrideRepuncModelPath=None):
    repuncModelPath = ""

    #This variable only exists to make pycharm figure out that the import is used.
    uselessVar:WordpieceTokenizer

    if overrideRepuncModelPath is None or overrideRepuncModelPath == "":
        print("Recase model path not set in config, checking if there is one in the working directory...")
        eligibleDirectories = list()
        for directory in os.listdir(os.getcwd()):
            if os.path.isdir(directory) and "vosk-recasepunc-" in directory:
                eligibleDirectories.append(directory)
        if len(eligibleDirectories) == 0:
            print("Could not automatically determine location of recasepunc model, please either put it in the same directory as the script or set the location in config.json")
            exit()
        elif len(eligibleDirectories) == 1:
            repuncModelPath = eligibleDirectories[0]
            repuncModelPath = os.path.join(repuncModelPath, "checkpoint")
        else:
            repuncModelPath = helper.chooseFromListOfStrings("Found multiple eligible repunc models.", eligibleDirectories)
            repuncModelPath = os.path.join(repuncModelPath, "checkpoint")
    else:
        repuncModelPath = overrideRepuncModelPath

    global predictor
    predictor = CasePuncPredictor(repuncModelPath, lang="en", flavor="bert-base-uncased")

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