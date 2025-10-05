@echo off
echo === Quick PyWin32 DLL Fix ===
echo.
echo This will fix the "DLL load failed while importing win32gui" error.
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Uninstalling problematic pywin32...
pip uninstall pywin32 -y

echo Installing fresh pywin32...
pip install pywin32==306

echo Testing pywin32...
python -c "import win32api, win32gui, win32process; print('SUCCESS: PyWin32 is working!')" 2>nul

if errorlevel 1 (
    echo.
    echo Still having issues. Trying alternative method...
    pip install --force-reinstall --no-cache-dir pywin32
    
    echo Testing again...
    python -c "import win32api, win32gui, win32process; print('SUCCESS: PyWin32 is working!')"
)

echo.
echo Fix complete! You can now run start_bot.bat or start_bot.ps1
echo.
pause