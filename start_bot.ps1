Write-Host "Starting Xbox Bot with Virtual Environment..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host ""
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Check if requirements are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import customtkinter, cv2, numpy, vgamepad, pygetwindow, PIL, psutil, pynput" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Basic dependencies missing"
    }
    
    # Check pywin32 separately as it often has DLL issues
    python -c "import win32api, win32gui, win32process" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "PyWin32 DLL issue detected. Running fix script..." -ForegroundColor Yellow
        python fix_pywin32.py
        throw "pywin32 fixed, please restart"
    }
    
    Write-Host "✓ All dependencies are installed" -ForegroundColor Green
}
catch {
    Write-Host "Installing/fixing required packages..." -ForegroundColor Yellow
    
    # Install basic requirements
    pip install -r requirements.txt
    
    # Fix pywin32 DLL registration issues
    Write-Host "Fixing pywin32 DLL registration..." -ForegroundColor Yellow
    try {
        # Uninstall and reinstall pywin32 to fix DLL issues
        pip uninstall pywin32 -y
        pip install pywin32
        
        # Try to register the DLLs
        python -c "import win32api; print('pywin32 working')"
        if ($LASTEXITCODE -ne 0) {
            # Alternative installation method
            Write-Host "Using alternative pywin32 installation..." -ForegroundColor Yellow
            pip install pywin32==306
        }
    }
    catch {
        Write-Host "⚠️ Warning: pywin32 might have issues. Some features may not work." -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Start the application
Write-Host "Starting Xbox Bot..." -ForegroundColor Green
Write-Host ""
python app.py

# Keep window open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error occurred. Press any key to exit..." -ForegroundColor Red
    Read-Host
}