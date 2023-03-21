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
	pip install -r requirements.txt
) else (
    call venv\scripts\activate
)

pip install --upgrade elevenlabslib

python speechToSpeech.py
