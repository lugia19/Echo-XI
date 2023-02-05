# speechToSpeechElevenLabs
Allows speech2speech with elevenlabs' TTS. Uses python 3.9 specifically due to the version requirements of recasepunc that I couldn't be bothered to fix.

It uses Vosk to do offline speech recognition.

Optionally uses [recasepunc](https://github.com/benob/recasepunc) to add punctuation and casing to improve the AI output.

Can synchronize the detected voice with an OBS text source using [obsws-python](https://pypi.org/project/obsws-python/).

