#!/usr/bin/env python3
"""
Test script for Stumble Bot
Validates that all modules can be imported and basic functionality works.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing module imports...")
    
    try:
        import customtkinter
        print("✓ customtkinter imported successfully")
    except ImportError as e:
        print(f"✗ customtkinter import failed: {e}")
        return False
    
    try:
        import cv2
        print("✓ opencv-python imported successfully")
    except ImportError as e:
        print(f"✗ opencv-python import failed: {e}")
        return False
    
    try:
        import numpy
        print("✓ numpy imported successfully")
    except ImportError as e:
        print(f"✗ numpy import failed: {e}")
        return False
    
    try:
        import vgamepad
        print("✓ vgamepad imported successfully")
    except ImportError as e:
        print(f"✗ vgamepad import failed: {e}")
        return False
    
    try:
        import pygetwindow
        print("✓ pygetwindow imported successfully")
    except ImportError as e:
        print(f"✗ pygetwindow import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow imported successfully")
    except ImportError as e:
        print(f"✗ Pillow import failed: {e}")
        return False
    
    try:
        import win32gui
        print("✓ pywin32 imported successfully")
    except ImportError as e:
        print(f"✗ pywin32 import failed: {e}")
        return False
    
    return True

def test_modules():
    """Test that our custom modules can be imported."""
    print("\nTesting custom modules...")
    
    try:
        from modules.window_manager import WindowManager
        print("✓ WindowManager imported successfully")
    except ImportError as e:
        print(f"✗ WindowManager import failed: {e}")
        return False
    
    try:
        from modules.image_detector import ImageDetector
        print("✓ ImageDetector imported successfully")
    except ImportError as e:
        print(f"✗ ImageDetector import failed: {e}")
        return False
    
    try:
        from modules.virtual_controller import VirtualController
        print("✓ VirtualController imported successfully")
    except ImportError as e:
        print(f"✗ VirtualController import failed: {e}")
        return False
    
    try:
        from modules.bot_thread import BotThread
        print("✓ BotThread imported successfully")
    except ImportError as e:
        print(f"✗ BotThread import failed: {e}")
        return False
    
    try:
        from modules.config_manager import ConfigManager
        print("✓ ConfigManager imported successfully")
    except ImportError as e:
        print(f"✗ ConfigManager import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of modules."""
    print("\nTesting basic functionality...")
    
    try:
        from modules.window_manager import WindowManager
        wm = WindowManager()
        print("✓ WindowManager instantiated successfully")
    except Exception as e:
        print(f"✗ WindowManager instantiation failed: {e}")
        return False
    
    try:
        from modules.image_detector import ImageDetector
        detector = ImageDetector()
        print("✓ ImageDetector instantiated successfully")
    except Exception as e:
        print(f"✗ ImageDetector instantiation failed: {e}")
        return False
    
    try:
        from modules.virtual_controller import VirtualController
        controller = VirtualController()
        if controller.is_connected():
            print("✓ VirtualController instantiated and connected successfully")
        else:
            print("⚠ VirtualController instantiated but not connected (this may be normal)")
    except Exception as e:
        print(f"✗ VirtualController instantiation failed: {e}")
        return False
    
    try:
        from modules.config_manager import ConfigManager
        config = ConfigManager()
        print("✓ ConfigManager instantiated successfully")
    except Exception as e:
        print(f"✗ ConfigManager instantiation failed: {e}")
        return False
    
    return True

def test_directory_structure():
    """Test that required directories exist or can be created."""
    print("\nTesting directory structure...")
    
    required_dirs = ['modules', 'templates', 'configs', 'logs']
    
    for directory in required_dirs:
        dir_path = current_dir / directory
        if dir_path.exists():
            print(f"✓ {directory}/ directory exists")
        else:
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"✓ {directory}/ directory created")
            except Exception as e:
                print(f"✗ Failed to create {directory}/ directory: {e}")
                return False
    
    return True

def test_gui():
    """Test basic GUI functionality (without showing window)."""
    print("\nTesting GUI components...")
    
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Don't show window
        root.destroy()
        print("✓ Basic tkinter functionality works")
    except Exception as e:
        print(f"✗ tkinter test failed: {e}")
        return False
    
    try:
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        print("✓ CustomTkinter basic functionality works")
    except Exception as e:
        print(f"✗ CustomTkinter test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("Stumble Bot - Installation Test")
    print("=" * 40)
    
    tests = [
        ("Import Tests", test_imports),
        ("Module Tests", test_modules),
        ("Directory Structure", test_directory_structure),
        ("Basic Functionality", test_basic_functionality),
        ("GUI Tests", test_gui)
    ]
    
    all_passed = True
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            print(traceback.format_exc())
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✓ All tests passed! Stumble Bot should work correctly.")
        print("\nTo start the application, run:")
        print("python main.py")
    else:
        print("✗ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Make sure you're using Python 3.7+")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. On Windows, you may need Visual C++ Redistributable for vgamepad")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())