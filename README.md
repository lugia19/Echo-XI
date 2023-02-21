# Speech to text to speech
Allows speech2speech with elevenlabs' TTS, using the `elevenlabslib` module.

Optionally uses [recasepunc](https://github.com/benob/recasepunc) to add punctuation and casing to improve the AI output.

Can synchronize the detected voice with an OBS text source using [obsws-python](https://pypi.org/project/obsws-python/).

## Installation and usage

Warning: Python 3.11 is still not fully supported by pytorch (but it should work on the nightly build). I'd recommend using python 3.10.6

Clone the repo: `git clone https://github.com/lugia19/speechToSpeechElevenLabs.git`

Create a venv (highly recommended): `python -m venv venv`

Activate the venv: `venv\Scripts\activate`

If you did it correctly, there should be (venv) at the start of the command line.

Install the requirements: `pip install -r requirements.txt`

Download a vosk model and a recasepunc model (I personally also use the vosk one for recasepunc).
They can be found at [here](https://alphacephei.com/vosk/models). For english I use `vosk-model-en-us-0.22` and `vosk-recasepunc-en-0.22`. Recasepunc is optional, but highly recommended to improve the output.

Place them both in the same directory as speech2speech.py. The resulting directory structure should be something like this:

```
venv
vosk-model-en-us-0.22
vosk-recasepunc-en-0.22
speech2speech.py
```

Run the script. It will ask you your API key (if you would like for it to not ask, you can add it to the config.json file) and for you to choose a voice to use. 

In addition, it will try to find the vosk models in the current directory. Everything should work fine if you followed the previous steps.

It will also prompt you asking if you would like to change your OBS-websocket settings. These are used for the OBS integration, where the detected text can be written to a text object for live subtitles.

Select your input and output and it should start, after asking you if you'd like to enable recasepunc and the OBS integration.
