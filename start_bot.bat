@echo off
echo Starting Xbox Bot with Virtual Environment...
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Check if requirements are installed
echo Checking dependencies...
python -c "import customtkinter, cv2, numpy, vgamepad, pygetwindow, PIL, psutil, pynput" 2>nul
if errorlevel 1 (
    echo Installing basic packages...
    pip install -r requirements.txt
)

REM Check pywin32 separately as it often has DLL issues
python -c "import win32api, win32gui, win32process" 2>nul
if errorlevel 1 (
    echo PyWin32 DLL issue detected. Running fix script...
    python fix_pywin32.py
    echo Please restart the bot after the fix completes.
    pause
    goto :eof
)

REM Start the application
echo Starting Xbox Bot...
echo.
python app.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause >nul
)