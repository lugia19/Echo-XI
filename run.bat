WHERE git
if %errorlevel% == 0 (
	if exist ".git" (
		git pull "https://github.com/lugia19/speechToSpeech.git"
	)
)

if not exist "venv" (
	python -m venv venv
	call venv\scripts\activate
	pip install wheel
	pip install numpy
	pip install -r requirements.txt
	pip install -r requirements-torch.txt
) else (
    call venv\scripts\activate
)

pip install --upgrade elevenlabslib
pip install faster_whisper

python speechToSpeech.py
