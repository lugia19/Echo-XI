# Speech to text to speech
Allows speech2speech with elevenlabs' TTS.

Optionally uses [recasepunc](https://github.com/benob/recasepunc) to add punctuation and casing to improve the AI output.

Can synchronize the detected voice with an OBS text source using [obsws-python](https://pypi.org/project/obsws-python/).

## Installation and usage

Warning: Python 3.11 is still not fully supported by pytorch (but it should work on the nightly build). I'd recommend using python 3.10.6

Clone the repo: `git clone https://github.com/lugia19/speechToSpeechElevenLabs.git`

Create a venv (highly recommended): `python -m venv venv`

Activate the venv: `venv\Scripts\activate`

If you did it correctly, there should be (venv) at the start of the command line.

Install the requirements: `pip install -r requirements.txt`

Run the script once to generate config.json (venv needs to be active): `python speechToSpeech.py`

Fill in the config.json file:
- api_key is your xi_api_key from elevenlabs
- vosk_model_path is the path to the directory containing the vosk voice recognition model ([download here](https://alphacephei.com/vosk/models), for english I use vosk-model-en-us-0.22)
- voice_ID is the ID of the voice you'd like to use. You can find them by going to the [API docs](https://api.elevenlabs.io/docs) and calling the `voices` endpoint, which will list all voices available to your account and their IDs. (This will be much easier in the future, once I actually start working on a python library for elevenlabs)
- obs_password and obs_port are the password and port for obs-websocket, if you're using the OBS integration for subtitles. WARNING: The script uses the V5 websocket API, so you'll want an up to date (V28 or newer) build of OBS with websocket built-in, rather than the plugin.
- repunc_model_path is the path to the model for recasepunc. I use the english one found on the same page as the normal vosk model.

Run it again, select your input and output and it should start.
