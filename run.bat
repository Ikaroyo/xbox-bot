@echo off
echo Stumble Bot - Game Automation Tool
echo ===================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    pause
    exit /b 1
)

REM Show Python version
echo Python version:
python --version
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

REM Check if requirements are installed by running test script
echo Running installation test...
python test_installation.py
if errorlevel 1 (
    echo.
    echo Installation test failed. Attempting to install dependencies...
    echo Installing requirements...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    echo.
    echo Re-running installation test...
    python test_installation.py
    if errorlevel 1 (
        echo.
        echo Installation still failing. Please check the error messages above.
        pause
        exit /b 1
    )
)

echo.
echo Starting Stumble Bot...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo Application exited with error. Check the logs folder for details.
    pause
)

echo.
echo Application closed.
pause