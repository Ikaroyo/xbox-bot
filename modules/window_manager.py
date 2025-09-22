"""
Window Manager Module

Handles window detection, selection, focusing and resizing operations.
Supports handling duplicate windows by showing process information.
"""

import pygetwindow as gw
import win32gui
import win32con
import win32process
import psutil
from typing import List, Dict, Optional, Tuple


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