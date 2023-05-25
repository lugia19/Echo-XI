# Echo-XI

## Info

The main goal of the project is to offer speech to text to speech.

**It now has a GUI, and it stores all the settings you input. Sensitive details such as API Keys are stored in the system keyring.**

In case you want to use the cli, simply call the script from the comamnd line with the argument --cli.

It offers three separate speech recognition services:
- Vosk, with [recasepunc](https://github.com/benob/recasepunc) to add punctuation
- Azure speech recognition
- Whisper, both running locally (**now using faster-whisper for faster recognition and lower VRAM usage**) and through openAI's API

In addition, it automatically translates the output into a language of the user's choosing (from those supported by ElevenLabs' multilingual model), if the user is speaking a different language.

Each speech recognition provider has different language support, so be sure to read the details.

Translation is provided via either DeepL for supported languages, or Google Translate.

The recognized and translated text is then sent to a TTS provider, of which two are supported:
- Elevenlabs, through the `elevenlabslib` module, a high quality but paid online TTS service that supports multiple languages.
- pyttsx3, a low quality TTS that runs locally.

The project also allows you to synchronize the detected text with an OBS text source using [obsws-python](https://pypi.org/project/obsws-python/).

## Installation and usage

Warning: Python 3.11 is still not fully supported by pytorch (but it should work on the nightly build). I'd recommend using python 3.10.6

Before anything else: you'll need to have ffmpeg in your $PATH. You can follow [this tutorial](https://phoenixnap.com/kb/ffmpeg-windows) if you're on windows

Additionally, if you're on linux, you'll need to make sure portaudio is installed.

On windows:

1) Clone the repo: `git clone https://github.com/lugia19/speechToSpeechElevenLabs.git`

2) Run run.bat - it will handle all the following steps for you.

Everywhere else:

1) Clone the repo: `git clone https://github.com/lugia19/speechToSpeechElevenLabs.git`

2) Create a venv: `python -m venv venv`

3) Activate the venv: `venv\Scripts\activate`

4) If you did it correctly, there should be (venv) at the start of the command line.

5) Install the requirements: `pip install -r requirements.txt`

6) Run it.


If you would like to use the voice on something like discord, use [VB-Cable](https://vb-audio.com/Cable/). In the script select your normal microphone as input, `VB-Cable input` as the output, then on discord select `VB-Cable output` as the input. Yes, it's a little confusing.

## Notes on vosk/recasepunc

If you're looking to use the vosk/recasepunc and you need something besides the included (downloadable) models, read on.

Vosk models can be found [here](https://alphacephei.com/vosk/models). The same page also offers some recasepunc models. For additional ones, you can look in the recasepunc repo.

For english I use `vosk-model-en-us-0.22` and `vosk-recasepunc-en-0.22`. Recasepunc is technically optional when using vosk, but highly recommended to improve the output.

The script looks for models under the models/vosk and models/recasepunc folders.

A typical folder structure would look something like this (recasepunc models can either be in their own folder or by themselves, depending on which source you download them from. Both are supported.):
```
-misc
-models
    -vosk
        -vosk-model-en-us-0.22
        -vosk-model-it-0.22
    -recasepunc
        -vosk-recasepunc-en-0.22
        it.22000
-speechRecognition
-ttsProviders
helper.py
speechToSpeech.py
```

For everything else, simply run the script and follow the instructions.

If you would like to use the voice on something like discord, use [VB-Cable](https://vb-audio.com/Cable/). In the script select your normal microphone as input, `VB-Cable input` as the output, then on discord select `VB-Cable output` as the input. Yes, it's a little confusing.
