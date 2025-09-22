"""
Window Manager Module

Handles window detection, selection, focusing and resizing operations.
Supports handling duplicate windows by showing process information.
"""

import pygetwindow as gw
import win32gui
import win32con
import win32process
import win32api
import win32ui
from win32con import *
import psutil
import ctypes
from ctypes import wintypes, Structure, c_long, c_ulong, c_short, c_ushort, c_byte, POINTER, byref, sizeof
import time
from typing import List, Dict, Optional, Tuple

# Windows API constants for input injection
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

# SendInput constants
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# Virtual Key codes for Xbox controller simulation
VK_GAMEPAD_A = 0x5A  # Z key (can be remapped by games)
VK_GAMEPAD_B = 0x58  # X key
VK_GAMEPAD_X = 0x43  # C key  
VK_GAMEPAD_Y = 0x56  # V key
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_SPACE = 0x20

# Input structures for SendInput
class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]

class MOUSEINPUT(Structure):
    _fields_ = [("dx", c_long), ("dy", c_long),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", POINTER(wintypes.ULONG))]

class KEYBDINPUT(Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", POINTER(wintypes.ULONG))]

class HARDWAREINPUT(Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class INPUT(Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT),
                    ("mi", MOUSEINPUT),
                    ("hi", HARDWAREINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD),
                ("_input", _INPUT)]

# Get Windows API functions
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


class WindowManager:
    """Manages game window operations including detection, focus, and resizing."""
    
    def __init__(self):
        self.current_window = None
        self.target_window_title = "Xbox"
        
    def find_windows_by_title(self, title: str) -> List[Dict]:
        """
        Find all windows that match the given title exactly.
        
        Args:
            title: Window title to search for
            
        Returns:
            List of dictionaries containing window information:
            - hwnd: Window handle
            - title: Window title  
            - pid: Process ID
            - process_name: Name of the process executable
        """
        windows = []
        
        def enum_windows_callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if window_title == title:
                    try:
                        # Get process information
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        process_name = process.name()
                        
                        windows_list.append({
                            'hwnd': hwnd,
                            'title': window_title,
                            'pid': pid,
                            'process_name': process_name
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # If we can't get process info, still add the window
                        windows_list.append({
                            'hwnd': hwnd,
                            'title': window_title,
                            'pid': None,
                            'process_name': 'Unknown'
                        })
        
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows
    
    def select_window(self, title: str) -> Optional[Dict]:
        """
        Select a window by title. If multiple windows exist, returns None
        to indicate user intervention is needed.
        
        Args:
            title: Window title to search for
            
        Returns:
            Window dict if single match found, None if multiple or no matches
        """
        windows = self.find_windows_by_title(title)
        
        if len(windows) == 0:
            return None
        elif len(windows) == 1:
            self.current_window = windows[0]
            return windows[0]
        else:
            # Multiple windows found - need user selection
            return None
    
    def select_window_by_pid(self, title: str, pid: int) -> Optional[Dict]:
        """
        Select a specific window by title and PID.
        
        Args:
            title: Window title
            pid: Process ID to match
            
        Returns:
            Window dict if found, None otherwise
        """
        windows = self.find_windows_by_title(title)
        
        for window in windows:
            if window['pid'] == pid:
                self.current_window = window
                return window
        
        return None
    
    def focus_window(self, window: Optional[Dict] = None) -> bool:
        """
        Bring the specified window (or current window) to the foreground.
        
        Args:
            window: Window dict, uses current_window if None
            
        Returns:
            True if successful, False otherwise
        """
        target_window = window or self.current_window
        
        if not target_window:
            return False
        
        try:
            hwnd = target_window['hwnd']
            
            # Check if window still exists
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Restore window if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to foreground
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
            
            return True
            
        except Exception as e:
            print(f"Error focusing window: {e}")
            return False
    
    def resize_window(self, width: int, height: int, window: Optional[Dict] = None) -> bool:
        """
        Resize the specified window (or current window) to the given dimensions.
        
        Args:
            width: Target width in pixels
            height: Target height in pixels  
            window: Window dict, uses current_window if None
            
        Returns:
            True if successful, False otherwise
        """
        target_window = window or self.current_window
        
        if not target_window:
            return False
        
        try:
            hwnd = target_window['hwnd']
            
            # Check if window still exists
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Get current window position
            rect = win32gui.GetWindowRect(hwnd)
            x, y = rect[0], rect[1]
            
            # Resize window
            win32gui.SetWindowPos(
                hwnd, 
                win32con.HWND_TOP,
                x, y, width, height,
                win32con.SWP_SHOWWINDOW
            )
            
            return True
            
        except Exception as e:
            print(f"Error resizing window: {e}")
            return False
    
    def get_window_rect(self, window: Optional[Dict] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the current window rectangle (x, y, width, height).
        
        Args:
            window: Window dict, uses current_window if None
            
        Returns:
            Tuple of (x, y, width, height) or None if failed
        """
        target_window = window or self.current_window
        
        if not target_window:
            return None
        
        try:
            hwnd = target_window['hwnd']
            
            if not win32gui.IsWindow(hwnd):
                return None
            
            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            width = right - x
            height = bottom - y
            
            return (x, y, width, height)
            
        except Exception as e:
            print(f"Error getting window rect: {e}")
            return None
    
    def capture_window_area(self, window: Optional[Dict] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the client area coordinates for screen capture.
        
        Args:
            window: Window dict, uses current_window if None
            
        Returns:
            Tuple of (x, y, width, height) for client area or None if failed
        """
        target_window = window or self.current_window
        
        if not target_window:
            return None
        
        try:
            hwnd = target_window['hwnd']
            
            if not win32gui.IsWindow(hwnd):
                return None
            
            # Get client area coordinates
            client_rect = win32gui.GetClientRect(hwnd)
            client_top_left = win32gui.ClientToScreen(hwnd, (client_rect[0], client_rect[1]))
            client_bottom_right = win32gui.ClientToScreen(hwnd, (client_rect[2], client_rect[3]))
            
            x = client_top_left[0]
            y = client_top_left[1]
            width = client_bottom_right[0] - client_top_left[0]
            height = client_bottom_right[1] - client_top_left[1]
            
            return (x, y, width, height)
            
        except Exception as e:
            print(f"Error getting window capture area: {e}")
            return None
    
    def is_window_valid(self, window: Optional[Dict] = None) -> bool:
        """
        Check if the specified window (or current window) is still valid.
        
        Args:
            window: Window dict, uses current_window if None
            
        Returns:
            True if window is valid, False otherwise
        """
        target_window = window or self.current_window
        
        if not target_window:
            return False
        
        try:
            hwnd = target_window['hwnd']
            return win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd)
        except:
            return False
    
    def send_key_to_window(self, key_code: int, window: Optional[Dict] = None, key_down: bool = True) -> bool:
        """
        Send a key press/release to a specific window by focusing it first.
        
        Args:
            key_code: Virtual key code to send
            window: Window dict, uses current_window if None
            key_down: True for key down, False for key up
            
        Returns:
            True if successful, False otherwise
        """
        target_window = window or self.current_window
        
        if not target_window:
            return False
            
        try:
            hwnd = target_window['hwnd']
            
            if not win32gui.IsWindow(hwnd):
                return False
            
            # Focus window first
            if not self._force_focus_window(hwnd):
                return False
            
            time.sleep(0.05)
            
            # Send input
            return self._send_input_direct(key_code, 0.1)
            
        except Exception as e:
            print(f"Error sending key to window: {e}")
            return False
    

    
    def send_robust_input_to_window(self, key_code: int, window: Optional[Dict] = None, duration: float = 0.1) -> bool:
        """
        Send input to window by focusing it first then using SendInput.
        
        Args:
            key_code: Virtual key code to send
            window: Window dict, uses current_window if None
            duration: How long to hold the key
            
        Returns:
            True if successful, False otherwise
        """
        target_window = window or self.current_window
        
        if not target_window:
            return False
            
        hwnd = target_window['hwnd']
        
        if not win32gui.IsWindow(hwnd):
            return False
        
        try:
            # Focus the window first
            if not self._force_focus_window(hwnd):
                return False
            
            time.sleep(0.05)  # Allow focus to settle
            
            # Send input using SendInput
            return self._send_input_direct(key_code, duration)
            
        except Exception as e:
            print(f"Error sending input: {e}")
            return False
    
    def _send_input_direct(self, key_code: int, duration: float) -> bool:
        """Send input using SendInput API."""
        try:
            # Create input structure for key down
            inputs = (INPUT * 2)()
            
            # Key down
            inputs[0].type = INPUT_KEYBOARD
            inputs[0].ki.wVk = key_code
            inputs[0].ki.wScan = 0
            inputs[0].ki.dwFlags = 0
            inputs[0].ki.time = 0
            inputs[0].ki.dwExtraInfo = None
            
            # Key up
            inputs[1].type = INPUT_KEYBOARD
            inputs[1].ki.wVk = key_code
            inputs[1].ki.wScan = 0
            inputs[1].ki.dwFlags = KEYEVENTF_KEYUP
            inputs[1].ki.time = 0
            inputs[1].ki.dwExtraInfo = None
            
            # Send key down
            result1 = user32.SendInput(1, byref(inputs[0]), sizeof(INPUT))
            
            # Hold for duration
            time.sleep(duration)
            
            # Send key up
            result2 = user32.SendInput(1, byref(inputs[1]), sizeof(INPUT))
            
            return result1 > 0 and result2 > 0
            
        except Exception as e:
            print(f"SendInput error: {e}")
            return False
    
    def _force_focus_window(self, hwnd: int) -> bool:
        """Force focus on a window."""
        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            
            # Bring to foreground
            win32gui.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            
            # Set focus
            user32.SetFocus(hwnd)
            
            # Small delay to let changes take effect
            time.sleep(0.02)
            
            # Verify focus
            focused_hwnd = user32.GetForegroundWindow()
            return focused_hwnd == hwnd
            
        except Exception as e:
            print(f"Force focus error: {e}")
            return False
    

    

    
    def prepare_window_for_input(self, window: Optional[Dict] = None) -> bool:
        """
        Prepare window to receive input by focusing it.
        
        Args:
            window: Window dict, uses current_window if None
            
        Returns:
            True if preparation successful, False otherwise
        """
        return self.focus_window(window)