@echo off
echo -----------------------------------
echo Setting up Penny virtual environment...
echo -----------------------------------

if not exist "venv" (
    echo Creating new virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing required packages...
pip install requests fastapi uvicorn pydub twitchio python-dotenv sounddevice scipy

if not exist "start_venv.bat" (
    echo Creating start_venv.bat helper...
    (
        echo @echo off
        echo cd /d "%%~dp0"
        echo call venv\Scripts\activate.bat
        echo cmd
    ) > start_venv.bat
    echo start_venv.bat created!
) else (
    echo start_venv.bat already exists.
)

echo -----------------------------------
echo Setup complete!
echo -----------------------------------
pause