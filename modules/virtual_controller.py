"""
Virtual Controller Module

Wrapper for vgamepad to simulate Xbox 360 controller input.
Provides simplified methods for button presses and joystick movements.
"""

import vgamepad as vg
import time
import random
from typing import Optional, Union, List, Tuple
from enum import Enum
import win32api
import win32con
import win32gui

# Additional constants for PostMessage clicking
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010


class InputMode(Enum):
    """Input mode for actions."""
    CONTROLLER = "controller"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"


class KeyboardKey(Enum):
    """Common keyboard keys for actions."""
    # Letters
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"
    
    # Numbers
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"
    
    # Special keys
    SPACE = "space"
    ENTER = "enter"
    TAB = "tab"
    ESCAPE = "esc"
    BACKSPACE = "backspace"
    DELETE = "delete"
    
    # Arrow keys
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    
    # Function keys
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"
    
    # Modifier keys
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    WIN = "win"
    
    # Other common keys
    HOME = "home"
    END = "end"
    PAGE_UP = "page up"
    PAGE_DOWN = "page down"
    INSERT = "insert"
    

class MouseButton(Enum):
    """Mouse button mappings."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    

class XboxButton(Enum):
    """Xbox 360 controller button mappings."""
    A = "A"
    B = "B"
    X = "X" 
    Y = "Y"
    LB = "LB"
    RB = "RB"
    BACK = "BACK"
    START = "START"
    DPAD_UP = "DPAD_UP"
    DPAD_DOWN = "DPAD_DOWN"
    DPAD_LEFT = "DPAD_LEFT"
    DPAD_RIGHT = "DPAD_RIGHT"
    LEFT_THUMB = "LEFT_THUMB"
    RIGHT_THUMB = "RIGHT_THUMB"
    LEFT_JOYSTICK = "LEFT_JOYSTICK"
    RIGHT_JOYSTICK = "RIGHT_JOYSTICK"
    # Trigger buttons
    LT = "LT"
    RT = "RT"
    # Left stick movement directions
    STICK_UP = "STICK_UP"
    STICK_DOWN = "STICK_DOWN"
    STICK_LEFT = "STICK_LEFT"
    STICK_RIGHT = "STICK_RIGHT"
    STICK_UP_LEFT = "STICK_UP_LEFT"
    STICK_UP_RIGHT = "STICK_UP_RIGHT"
    STICK_DOWN_LEFT = "STICK_DOWN_LEFT"
    STICK_DOWN_RIGHT = "STICK_DOWN_RIGHT"
    STICK_CENTER = "STICK_CENTER" 


class VirtualController:
    """Handles Xbox 360 controller simulation, keyboard input, and mouse input."""
    
    def __init__(self):
        """
        Initialize the virtual Xbox 360 controller.
        """
        try:
            self.gamepad = vg.VX360Gamepad()
            self.connected = True
            print("Virtual Xbox 360 controller initialized successfully")
        except Exception as e:
            print(f"Error initializing virtual controller: {e}")
            self.gamepad = None
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if the virtual controller is connected."""
        return self.connected and self.gamepad is not None
    
    # === KEYBOARD INPUT METHODS ===
    
    def press_key(self, key: Union[str, KeyboardKey], duration: float = 0.1) -> bool:
        """
        Press and release a keyboard key.
        
        Args:
            key: Key to press (string or KeyboardKey enum)
            duration: How long to hold the key (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to string if enum
            if isinstance(key, KeyboardKey):
                key_str = key.value
            else:
                key_str = str(key).lower()
            
            # Map special keys to virtual key codes
            vk_code = self._get_virtual_key_code(key_str)
            if vk_code is None:
                print(f"Unsupported key: {key_str}")
                return False
            
            # Press key
            win32api.keybd_event(vk_code, 0, 0, 0)
            time.sleep(duration)
            
            # Release key
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            return True
            
        except Exception as e:
            print(f"Error pressing key {key}: {e}")
            return False
    
    def press_key_combo(self, keys: List[Union[str, KeyboardKey]], duration: float = 0.1) -> bool:
        """
        Press multiple keys simultaneously (key combination).
        
        Args:
            keys: List of keys to press together
            duration: How long to hold the keys (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to virtual key codes
            vk_codes = []
            for key in keys:
                if isinstance(key, KeyboardKey):
                    key_str = key.value
                else:
                    key_str = str(key).lower()
                
                vk_code = self._get_virtual_key_code(key_str)
                if vk_code is None:
                    print(f"Unsupported key in combo: {key_str}")
                    return False
                vk_codes.append(vk_code)
            
            # Press all keys
            for vk_code in vk_codes:
                win32api.keybd_event(vk_code, 0, 0, 0)
            
            time.sleep(duration)
            
            # Release all keys (in reverse order)
            for vk_code in reversed(vk_codes):
                win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            return True
            
        except Exception as e:
            print(f"Error pressing key combo {keys}: {e}")
            return False
    
    def type_text(self, text: str, delay: float = 0.05) -> bool:
        """
        Type text by simulating individual key presses.
        
        Args:
            text: Text to type
            delay: Delay between key presses
            
        Returns:
            True if successful, False otherwise
        """
        try:
            for char in text:
                if char == ' ':
                    self.press_key(KeyboardKey.SPACE, delay)
                elif char == '\\n':
                    self.press_key(KeyboardKey.ENTER, delay)
                elif char == '\\t':
                    self.press_key(KeyboardKey.TAB, delay)
                else:
                    # For regular characters, use Unicode input
                    win32api.keybd_event(0, 0, win32con.KEYEVENTF_UNICODE, ord(char))
                    time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"Error typing text '{text}': {e}")
            return False
    
    def _get_virtual_key_code(self, key_str: str) -> Optional[int]:
        """
        Get Windows virtual key code for a key string.
        
        Args:
            key_str: Key string
            
        Returns:
            Virtual key code or None if not found
        """
        # Common virtual key codes
        key_map = {
            # Letters (A-Z)
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
            'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
            'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
            'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
            'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
            
            # Numbers (0-9)
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            
            # Special keys
            'space': win32con.VK_SPACE,
            'enter': win32con.VK_RETURN,
            'tab': win32con.VK_TAB,
            'esc': win32con.VK_ESCAPE,
            'escape': win32con.VK_ESCAPE,
            'backspace': win32con.VK_BACK,
            'delete': win32con.VK_DELETE,
            
            # Arrow keys
            'up': win32con.VK_UP,
            'down': win32con.VK_DOWN,
            'left': win32con.VK_LEFT,
            'right': win32con.VK_RIGHT,
            
            # Function keys
            'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3,
            'f4': win32con.VK_F4, 'f5': win32con.VK_F5, 'f6': win32con.VK_F6,
            'f7': win32con.VK_F7, 'f8': win32con.VK_F8, 'f9': win32con.VK_F9,
            'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,
            
            # Modifier keys
            'ctrl': win32con.VK_CONTROL,
            'alt': win32con.VK_MENU,
            'shift': win32con.VK_SHIFT,
            'win': win32con.VK_LWIN,
            
            # Other keys
            'home': win32con.VK_HOME,
            'end': win32con.VK_END,
            'page up': win32con.VK_PRIOR,
            'page down': win32con.VK_NEXT,
            'insert': win32con.VK_INSERT,
        }
        
        return key_map.get(key_str.lower())
    
    # === MOUSE INPUT METHODS ===
    
    def click_mouse(self, button: Union[str, MouseButton] = MouseButton.LEFT, x: Optional[int] = None, y: Optional[int] = None, hwnd: Optional[int] = None) -> bool:
        """
        Click mouse button at current position or specified coordinates.
        
        Args:
            button: Mouse button to click
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            hwnd: Window handle for unfocused window clicking (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to string if enum
            if isinstance(button, MouseButton):
                button_str = button.value
            else:
                button_str = str(button).lower()
            
            # Get current cursor position if coordinates not provided
            if x is None or y is None:
                current_x, current_y = win32gui.GetCursorPos()
                if x is None:
                    x = current_x
                if y is None:
                    y = current_y
            
            # Add human-like random offset to coordinates (±3 pixels)
            human_offset_x = random.randint(-3, 3)
            human_offset_y = random.randint(-3, 3)
            x += human_offset_x
            y += human_offset_y
            
            # Always move cursor to target location first for visual feedback and accuracy
            print(f"Moving cursor to ({x}, {y}) [offset: {human_offset_x}, {human_offset_y}] and clicking {button_str} button")
            win32api.SetCursorPos((x, y))
            
            # Small delay to ensure cursor movement is complete
            time.sleep(0.01)
            
            # Try PostMessage for unfocused window clicking if hwnd provided
            if hwnd:
                try:
                    # Convert screen coordinates to client coordinates
                    client_x, client_y = win32gui.ScreenToClient(hwnd, (x, y))
                    lparam = (client_y << 16) | (client_x & 0xFFFF)
                    
                    # Map button to messages  
                    if button_str == 'left':
                        win32gui.PostMessage(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
                        win32gui.PostMessage(hwnd, WM_LBUTTONUP, 0, lparam)
                    elif button_str == 'right':
                        win32gui.PostMessage(hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
                        win32gui.PostMessage(hwnd, WM_RBUTTONUP, 0, lparam)
                    elif button_str == 'middle':
                        win32gui.PostMessage(hwnd, WM_MBUTTONDOWN, MK_MBUTTON, lparam)
                        win32gui.PostMessage(hwnd, WM_MBUTTONUP, 0, lparam)
                    else:
                        return False
                    
                    print(f"PostMessage click sent to window {hwnd} at client coords ({client_x}, {client_y}) after cursor move")
                    return True
                    
                except Exception as e:
                    print(f"PostMessage click failed, falling back to mouse_event: {e}")
                    # Fall through to mouse_event method
            
            # Standard method - perform click at current cursor position (already moved above)
            # Map button to mouse events
            if button_str == 'left':
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
            elif button_str == 'right':
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, x, y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, x, y, 0, 0)
            elif button_str == 'middle':
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, x, y, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, x, y, 0, 0)
            else:
                print(f"Unsupported mouse button: {button_str}")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error clicking mouse {button} at ({x}, {y}): {e}")
            return False
    
    def double_click_mouse(self, button: Union[str, MouseButton] = MouseButton.LEFT, x: Optional[int] = None, y: Optional[int] = None, hwnd: Optional[int] = None) -> bool:
        """
        Double-click mouse button.
        
        Args:
            button: Mouse button to double-click
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add small random delay between clicks to simulate human timing
            click_delay = random.uniform(0.05, 0.15)  # 50-150ms between clicks
            
            success1 = self.click_mouse(button, x, y, hwnd)
            time.sleep(click_delay)  # Human-like delay between clicks
            success2 = self.click_mouse(button, x, y, hwnd)
            return success1 and success2
            
        except Exception as e:
            print(f"Error double-clicking mouse {button}: {e}")
            return False
    
    def move_mouse(self, x: int, y: int) -> bool:
        """
        Move mouse to specified coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            win32api.SetCursorPos((x, y))
            return True
            
        except Exception as e:
            print(f"Error moving mouse to ({x}, {y}): {e}")
            return False
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        try:
            return win32gui.GetCursorPos()
        except Exception as e:
            print(f"Error getting mouse position: {e}")
            return (0, 0)
    
    def scroll_mouse(self, direction: str, amount: int = 3) -> bool:
        """
        Scroll mouse wheel.
        
        Args:
            direction: 'up' or 'down'
            amount: Number of scroll steps
            
        Returns:
            True if successful, False otherwise
        """
        try:
            x, y = self.get_mouse_position()
            
            if direction.lower() == 'up':
                scroll_delta = amount * 120  # Positive for up
            elif direction.lower() == 'down':
                scroll_delta = -amount * 120  # Negative for down
            else:
                print(f"Invalid scroll direction: {direction}")
                return False
            
            win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, x, y, scroll_delta, 0)
            return True
            
        except Exception as e:
            print(f"Error scrolling mouse {direction}: {e}")
            return False
    

    
    def press_button(self, button: XboxButton, duration: float = 0.1) -> bool:
        """
        Press and release a controller button or execute a joystick movement.
        
        Args:
            button: XboxButton enum value
            duration: How long to hold the button (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Check if it's a trigger
            if button == XboxButton.LT:
                # Press left trigger
                self.gamepad.left_trigger_float(value_float=1.0)
                self.gamepad.update()
                time.sleep(duration)
                self.gamepad.left_trigger_float(value_float=0.0)
                self.gamepad.update()
                return True
            elif button == XboxButton.RT:
                # Press right trigger
                self.gamepad.right_trigger_float(value_float=1.0)
                self.gamepad.update()
                time.sleep(duration)
                self.gamepad.right_trigger_float(value_float=0.0)
                self.gamepad.update()
                return True
            
            # Check if it's a stick movement
            stick_movements = {
                XboxButton.STICK_UP: "up",
                XboxButton.STICK_DOWN: "down", 
                XboxButton.STICK_LEFT: "left",
                XboxButton.STICK_RIGHT: "right",
                XboxButton.STICK_UP_LEFT: "up-left",
                XboxButton.STICK_UP_RIGHT: "up-right",
                XboxButton.STICK_DOWN_LEFT: "down-left",
                XboxButton.STICK_DOWN_RIGHT: "down-right",
                XboxButton.STICK_CENTER: "center"
            }
            
            if button in stick_movements:
                return self.move_left_stick(stick_movements[button], 1.0, duration)
            
            # Map button enum to vgamepad constants
            button_map = {
                XboxButton.A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                XboxButton.B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                XboxButton.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                XboxButton.Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                XboxButton.LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                XboxButton.RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                XboxButton.BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                XboxButton.START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                XboxButton.LEFT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                XboxButton.RIGHT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                XboxButton.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                XboxButton.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                XboxButton.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                XboxButton.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
            }
            
            if button not in button_map:
                print(f"Unknown button: {button}")
                return False
            
            vg_button = button_map[button]
            
            # Press button
            self.gamepad.press_button(button=vg_button)
            self.gamepad.update()
            
            # Hold for specified duration
            time.sleep(duration)
            
            # Release button
            self.gamepad.release_button(button=vg_button)
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error pressing button {button.value}: {e}")
            return False
    

    
    def press_button_combo(self, buttons: list, duration: float = 0.1) -> bool:
        """
        Press multiple buttons simultaneously.
        
        Args:
            buttons: List of XboxButton enum values
            duration: How long to hold the buttons (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            button_map = {
                XboxButton.A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                XboxButton.B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                XboxButton.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                XboxButton.Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                XboxButton.LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                XboxButton.RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                XboxButton.BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                XboxButton.START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                XboxButton.LEFT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                XboxButton.RIGHT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                XboxButton.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                XboxButton.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                XboxButton.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                XboxButton.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
            }
            
            # Press all buttons
            vg_buttons = []
            for button in buttons:
                if button in button_map:
                    vg_button = button_map[button]
                    self.gamepad.press_button(button=vg_button)
                    vg_buttons.append(vg_button)
                else:
                    print(f"Unknown button in combo: {button}")
            
            self.gamepad.update()
            
            # Hold for specified duration
            time.sleep(duration)
            
            # Release all buttons
            for vg_button in vg_buttons:
                self.gamepad.release_button(button=vg_button)
            
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error pressing button combo: {e}")
            return False
    
    def set_left_joystick(self, x: float, y: float) -> bool:
        """
        Set left joystick position.
        
        Args:
            x: X-axis value (-1.0 to 1.0, left to right)
            y: Y-axis value (-1.0 to 1.0, down to up)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Clamp values to valid range
            x = max(-1.0, min(1.0, x))
            y = max(-1.0, min(1.0, y))
            
            self.gamepad.left_joystick_float(x_value_float=x, y_value_float=y)
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error setting left joystick: {e}")
            return False
    
    def set_right_joystick(self, x: float, y: float) -> bool:
        """
        Set right joystick position.
        
        Args:
            x: X-axis value (-1.0 to 1.0, left to right)
            y: Y-axis value (-1.0 to 1.0, down to up)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Clamp values to valid range
            x = max(-1.0, min(1.0, x))
            y = max(-1.0, min(1.0, y))
            
            self.gamepad.right_joystick_float(x_value_float=x, y_value_float=y)
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error setting right joystick: {e}")
            return False
    
    def set_triggers(self, left: float = 0.0, right: float = 0.0) -> bool:
        """
        Set trigger values.
        
        Args:
            left: Left trigger value (0.0 to 1.0)
            right: Right trigger value (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Clamp values to valid range
            left = max(0.0, min(1.0, left))
            right = max(0.0, min(1.0, right))
            
            self.gamepad.left_trigger_float(value_float=left)
            self.gamepad.right_trigger_float(value_float=right)
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error setting triggers: {e}")
            return False
    
    def reset_controller(self) -> bool:
        """
        Reset all controller inputs to neutral/released state.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            self.gamepad.reset()
            self.gamepad.update()
            return True
            
        except Exception as e:
            print(f"Error resetting controller: {e}")
            return False
    
    def execute_action(self, action: str, input_mode: InputMode = InputMode.CONTROLLER, hwnd: Optional[int] = None) -> bool:
        """
        Execute an action based on input mode.
        
        Args:
            action: Action string (button name, key name, mouse action, or sequence)
            input_mode: Input mode to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if input_mode == InputMode.CONTROLLER:
                # Check if it's a sequence
                if ',' in action and ':' in action:
                    return self.execute_sequence(action)
                else:
                    # Single button press (might include duration)
                    if ':' in action and not ',' in action:
                        # Single button with duration (e.g., "STICK_UP:1")
                        parts = action.split(':')
                        if len(parts) == 2:
                            button_name, duration_str = parts
                            try:
                                duration = float(duration_str)
                                button = self.get_button_from_string(button_name)
                                if button:
                                    return self.press_button(button, duration)
                                else:
                                    print(f"Unknown controller button: {button_name}")
                                    return False
                            except ValueError:
                                print(f"Invalid duration in action: {action}")
                                return False
                    
                    # Simple button press without duration
                    button = self.get_button_from_string(action)
                    if button:
                        return self.press_button(button)
                    else:
                        print(f"Unknown controller button: {action}")
                        return False
            
            elif input_mode == InputMode.KEYBOARD:
                # Check if it's a key combination or sequence
                if '+' in action:
                    # Key combination (e.g., "ctrl+c", "alt+tab")
                    keys = action.split('+')
                    return self.press_key_combo(keys)
                elif ',' in action and ':' in action:
                    # Sequence (e.g., "w:2.0,a:1.0,d:1.0")
                    return self.execute_keyboard_sequence(action)
                else:
                    # Single key press
                    return self.press_key(action)
            
            elif input_mode == InputMode.MOUSE:
                # Parse mouse action
                if action.startswith('click'):
                    # Format: "click", "click:left", "click:right:100:200"
                    parts = action.split(':')
                    button = MouseButton.LEFT
                    x, y = None, None
                    
                    if len(parts) > 1 and parts[1]:
                        button = MouseButton(parts[1])
                    if len(parts) > 3:
                        x, y = int(parts[2]), int(parts[3])
                    
                    return self.click_mouse(button, x, y, hwnd)
                
                elif action.startswith('doubleclick'):
                    # Format: "doubleclick", "doubleclick:left:100:200"
                    parts = action.split(':')
                    button = MouseButton.LEFT
                    x, y = None, None
                    
                    if len(parts) > 1 and parts[1]:
                        button = MouseButton(parts[1])
                    if len(parts) > 3:
                        x, y = int(parts[2]), int(parts[3])
                    
                    return self.double_click_mouse(button, x, y, hwnd)
                
                elif action.startswith('move'):
                    # Format: "move:100:200"
                    parts = action.split(':')
                    if len(parts) >= 3:
                        x, y = int(parts[1]), int(parts[2])
                        return self.move_mouse(x, y)
                    else:
                        print(f"Invalid mouse move format: {action}")
                        return False
                
                elif action.startswith('scroll'):
                    # Format: "scroll:up", "scroll:down:5"
                    parts = action.split(':')
                    if len(parts) >= 2:
                        direction = parts[1]
                        amount = int(parts[2]) if len(parts) > 2 else 3
                        return self.scroll_mouse(direction, amount)
                    else:
                        print(f"Invalid mouse scroll format: {action}")
                        return False
                
                else:
                    print(f"Unknown mouse action: {action}")
                    return False
            
            else:
                print(f"Unknown input mode: {input_mode}")
                return False
                
        except Exception as e:
            print(f"Error executing action '{action}' with mode {input_mode}: {e}")
            return False
    
    def execute_keyboard_sequence(self, sequence_string: str) -> bool:
        """
        Execute a sequence of keyboard actions.
        
        Sequence format: "KEY1:duration,KEY2:duration,COMBO1+COMBO2:duration"
        Example: "w:2.0,ctrl+c:0.1,v:0.1"
        
        Args:
            sequence_string: Comma-separated sequence of key:duration pairs
            
        Returns:
            True if successful, False otherwise
        """
        try:
            steps = sequence_string.split(',')
            
            for step in steps:
                step = step.strip()
                if ':' not in step:
                    print(f"Invalid keyboard sequence step format: {step}")
                    continue
                
                action, duration_str = step.split(':', 1)
                action = action.strip()
                
                try:
                    duration = float(duration_str.strip())
                except ValueError:
                    print(f"Invalid duration in keyboard sequence: {duration_str}")
                    continue
                
                # Check if it's a key combination
                if '+' in action:
                    keys = action.split('+')
                    success = self.press_key_combo(keys, duration)
                else:
                    success = self.press_key(action, duration)
                
                if success:
                    print(f"Keyboard sequence: {action} for {duration}s")
                else:
                    print(f"Failed to execute keyboard action: {action}")
                    return False
                
                # Small delay between sequence steps
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"Error executing keyboard sequence '{sequence_string}': {e}")
            return False
    
    def execute_sequence(self, sequence_string: str) -> bool:
        """
        Execute a sequence of button presses with durations.
        
        Sequence format: "BUTTON1:duration,BUTTON2:duration,BUTTON3:duration"
        Example: "DPAD_UP:2.0,DPAD_LEFT:1.5,DPAD_RIGHT:1.0"
        
        Args:
            sequence_string: Comma-separated sequence of button:duration pairs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Parse the sequence string
            steps = sequence_string.split(',')
            
            for step in steps:
                step = step.strip()
                if ':' not in step:
                    print(f"Invalid sequence step format: {step}")
                    continue
                
                button_name, duration_str = step.split(':', 1)
                button_name = button_name.strip()
                
                try:
                    duration = float(duration_str.strip())
                except ValueError:
                    print(f"Invalid duration in sequence: {duration_str}")
                    continue
                
                # Get button enum
                button = self.get_button_from_string(button_name)
                if button is None:
                    print(f"Unknown button in sequence: {button_name}")
                    continue
                
                # Execute button press with duration
                if self.hold_button(button, duration):
                    print(f"Sequence: {button_name} held for {duration}s")
                else:
                    print(f"Failed to hold {button_name} in sequence")
                    return False
                
                # Small delay between sequence steps
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"Error executing sequence '{sequence_string}': {e}")
            return False
    
    def hold_button(self, button: XboxButton, duration: float) -> bool:
        """
        Hold a button down for a specific duration or execute a joystick movement.
        
        Args:
            button: XboxButton enum value
            duration: How long to hold the button (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Check if it's a stick movement
            stick_movements = {
                XboxButton.STICK_UP: "up",
                XboxButton.STICK_DOWN: "down", 
                XboxButton.STICK_LEFT: "left",
                XboxButton.STICK_RIGHT: "right",
                XboxButton.STICK_UP_LEFT: "up-left",
                XboxButton.STICK_UP_RIGHT: "up-right",
                XboxButton.STICK_DOWN_LEFT: "down-left",
                XboxButton.STICK_DOWN_RIGHT: "down-right",
                XboxButton.STICK_CENTER: "center"
            }
            
            if button in stick_movements:
                return self.move_left_stick(stick_movements[button], 1.0, duration)
            
            # Map button enum to vgamepad constants
            button_map = {
                XboxButton.A: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                XboxButton.B: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                XboxButton.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                XboxButton.Y: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                XboxButton.LB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                XboxButton.RB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                XboxButton.BACK: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                XboxButton.START: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
                XboxButton.LEFT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
                XboxButton.RIGHT_THUMB: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
                XboxButton.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
                XboxButton.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
                XboxButton.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
                XboxButton.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
            }
            
            if button not in button_map:
                print(f"Unknown button: {button}")
                return False
            
            vg_button = button_map[button]
            
            # Press and hold button
            self.gamepad.press_button(button=vg_button)
            self.gamepad.update()
            
            # Hold for specified duration
            time.sleep(duration)
            
            # Release button
            self.gamepad.release_button(button=vg_button)
            self.gamepad.update()
            
            return True
            
        except Exception as e:
            print(f"Error holding button {button.value}: {e}")
            return False
    
    def get_button_from_string(self, button_str: str) -> Optional[XboxButton]:
        """
        Convert a string to XboxButton enum.
        
        Args:
            button_str: String representation of the button
            
        Returns:
            XboxButton enum or None if not found
        """
        button_str = button_str.upper()
        
        try:
            return XboxButton(button_str)
        except ValueError:
            return None
    
    def get_available_buttons(self) -> list:
        """
        Get list of all available button names.
        
        Returns:
            List of button name strings
        """
        return [button.value for button in XboxButton]
    
    def move_left_stick(self, direction: str, intensity: float = 1.0, duration: float = 0.1) -> bool:
        """
        Move left joystick in a specific direction.
        
        Args:
            direction: Direction to move ("up", "down", "left", "right", "up-left", "up-right", "down-left", "down-right", "center")
            intensity: Movement intensity (0.0 to 1.0)
            duration: How long to hold the movement (seconds)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Clamp intensity
            intensity = max(0.0, min(1.0, intensity))
            
            # Direction mappings
            direction_map = {
                "center": (0.0, 0.0),
                "up": (0.0, intensity),
                "down": (0.0, -intensity),
                "left": (-intensity, 0.0),
                "right": (intensity, 0.0),
                "up-left": (-intensity * 0.7071, intensity * 0.7071),     # 45 degree angle
                "up-right": (intensity * 0.7071, intensity * 0.7071),
                "down-left": (-intensity * 0.7071, -intensity * 0.7071),
                "down-right": (intensity * 0.7071, -intensity * 0.7071)
            }
            
            if direction.lower() not in direction_map:
                print(f"Unknown direction: {direction}")
                return False
            
            x, y = direction_map[direction.lower()]
            
            # Set joystick position
            self.set_left_joystick(x, y)
            
            # Hold for specified duration
            time.sleep(duration)
            
            # Return to center
            self.set_left_joystick(0.0, 0.0)
            
            return True
            
        except Exception as e:
            print(f"Error moving left stick {direction}: {e}")
            return False
    
    def execute_movement_sequence(self, sequence_string: str) -> bool:
        """
        Execute a sequence of joystick movements.
        
        Sequence format: "DIRECTION:duration,DIRECTION:duration"
        Example: "up:2.0,left:1.5,right:1.0"
        Directions: up, down, left, right, up-left, up-right, down-left, down-right, center
        
        Args:
            sequence_string: Comma-separated sequence of direction:duration pairs
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        try:
            # Parse the sequence string
            steps = sequence_string.split(',')
            
            for step in steps:
                step = step.strip()
                if ':' not in step:
                    print(f"Invalid movement sequence step format: {step}")
                    continue
                
                direction, duration_str = step.split(':', 1)
                direction = direction.strip()
                
                try:
                    duration = float(duration_str.strip())
                except ValueError:
                    print(f"Invalid duration in movement sequence: {duration_str}")
                    continue
                
                # Execute movement
                if self.move_left_stick(direction, 1.0, duration):
                    print(f"Movement sequence: {direction} for {duration}s")
                else:
                    print(f"Failed to execute movement: {direction}")
                    return False
                
                # Small delay between sequence steps
                time.sleep(0.1)
            
            return True
            
        except Exception as e:
            print(f"Error executing movement sequence '{sequence_string}': {e}")
            return False
    
    # === CONVENIENCE METHODS ===
    
    def get_available_keys(self) -> List[str]:
        """
        Get list of all available keyboard key names.
        
        Returns:
            List of key name strings
        """
        return [key.value for key in KeyboardKey]
    
    def get_available_mouse_buttons(self) -> List[str]:
        """
        Get list of all available mouse button names.
        
        Returns:
            List of mouse button name strings
        """
        return [button.value for button in MouseButton]
    
    def get_input_mode_from_string(self, mode_str: str) -> Optional[InputMode]:
        """
        Convert a string to InputMode enum.
        
        Args:
            mode_str: String representation of the input mode
            
        Returns:
            InputMode enum or None if not found
        """
        mode_str = mode_str.lower()
        try:
            return InputMode(mode_str)
        except ValueError:
            return None
    
    # === COMMON KEY COMBINATION SHORTCUTS ===
    
    def copy(self) -> bool:
        """Ctrl+C shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.C])
    
    def paste(self) -> bool:
        """Ctrl+V shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.V])
    
    def cut(self) -> bool:
        """Ctrl+X shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.X])
    
    def select_all(self) -> bool:
        """Ctrl+A shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.A])
    
    def undo(self) -> bool:
        """Ctrl+Z shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.Z])
    
    def redo(self) -> bool:
        """Ctrl+Y shortcut."""
        return self.press_key_combo([KeyboardKey.CTRL, KeyboardKey.Y])
    
    def alt_tab(self) -> bool:
        """Alt+Tab shortcut."""
        return self.press_key_combo([KeyboardKey.ALT, KeyboardKey.TAB])
    
    def alt_f4(self) -> bool:
        """Alt+F4 shortcut."""
        return self.press_key_combo([KeyboardKey.ALT, KeyboardKey.F4])
    
    def win_key(self) -> bool:
        """Windows key press."""
        return self.press_key(KeyboardKey.WIN)

    def test_all_buttons(self, duration: float = 0.1) -> bool:
        """
        Test all buttons by pressing them sequentially.
        Useful for debugging and verification.
        
        Args:
            duration: How long to hold each button
            
        Returns:
            True if all tests successful, False otherwise
        """
        if not self.is_connected():
            return False
        
        print("Testing all controller buttons...")
        
        for button in XboxButton:
            print(f"Testing button: {button.value}")
            if not self.press_button(button, duration):
                print(f"Failed to test button: {button.value}")
                return False
            time.sleep(0.1)  # Small delay between tests
        
        print("All button tests completed successfully")
        return True