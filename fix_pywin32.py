"""
Fix PyWin32 DLL Issues

This script fixes common pywin32 DLL loading issues on Windows.
Run this if you get "DLL load failed while importing win32gui" errors.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {description} - SUCCESS")
            return True
        else:
            print(f"✗ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ {description} - ERROR: {e}")
        return False

def fix_pywin32():
    """Fix pywin32 DLL registration issues."""
    
    print("=== PyWin32 DLL Fix Script ===")
    print("This script will fix common pywin32 DLL loading issues.")
    print("")
    
    # Check if we're in a virtual environment
    venv_path = os.path.join(os.getcwd(), ".venv")
    if os.path.exists(venv_path):
        print("✓ Virtual environment detected")
        activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
        if os.path.exists(activate_script):
            print("✓ Activation script found")
        else:
            print("⚠️ Activation script not found, using system Python")
    else:
        print("⚠️ No virtual environment found, using system Python")
    
    # Method 1: Uninstall and reinstall pywin32
    print("\n--- Method 1: Clean Reinstall ---")
    run_command("pip uninstall pywin32 -y", "Uninstalling pywin32")
    run_command("pip install pywin32==306", "Installing pywin32 v306")
    
    # Method 2: Try to register DLLs using postinstall script
    print("\n--- Method 2: Register DLLs ---")
    try:
        import win32api
        print("✓ pywin32 import successful after reinstall")
    except ImportError:
        print("✗ pywin32 still not working, trying DLL registration...")
        
        # Try to run the postinstall script
        python_path = sys.executable
        python_dir = os.path.dirname(python_path)
        
        # Common locations for the postinstall script
        possible_paths = [
            os.path.join(python_dir, "Scripts", "pywin32_postinstall.py"),
            os.path.join(python_dir, "Lib", "site-packages", "pywin32_system32"),
            os.path.join(os.getcwd(), ".venv", "Scripts", "pywin32_postinstall.py"),
            os.path.join(os.getcwd(), ".venv", "Lib", "site-packages", "pywin32_system32"),
        ]
        
        for script_path in possible_paths:
            if os.path.exists(script_path):
                if script_path.endswith(".py"):
                    run_command(f"python \"{script_path}\" -install", "Running pywin32 postinstall")
                else:
                    print(f"Found pywin32_system32 directory: {script_path}")
                break
        else:
            print("⚠️ Could not find pywin32 postinstall script")
    
    # Method 3: Alternative installation
    print("\n--- Method 3: Alternative Installation ---")
    run_command("pip install --force-reinstall --no-cache-dir pywin32", "Force reinstall pywin32")
    
    # Final test
    print("\n--- Final Test ---")
    try:
        import win32api
        import win32gui
        import win32process
        print("✓ SUCCESS: All pywin32 modules imported successfully!")
        return True
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        print("\n--- Alternative Solutions ---")
        print("1. Try running as Administrator")
        print("2. Install Visual C++ Redistributables")
        print("3. Use conda instead of pip: conda install pywin32")
        print("4. Try older version: pip install pywin32==227")
        return False

if __name__ == "__main__":
    success = fix_pywin32()
    
    print("\n" + "="*50)
    if success:
        print("✓ PyWin32 fix completed successfully!")
        print("✓ You can now run the Xbox Bot normally.")
    else:
        print("⚠️ PyWin32 fix incomplete.")
        print("⚠️ The app will run with limited functionality.")
    
    input("\nPress Enter to continue...")