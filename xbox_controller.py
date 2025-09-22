"""
Xbox Controller Simulation Module
Provides Xbox controller input simulation for Windows using xinput
"""

import time
import ctypes
from ctypes import wintypes, Structure, c_ubyte, c_short, c_ushort
import random
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# XInput constants
XINPUT_GAMEPAD_DPAD_UP = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT = 0x0008
XINPUT_GAMEPAD_START = 0x0010
XINPUT_GAMEPAD_BACK = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A = 0x1000
XINPUT_GAMEPAD_B = 0x2000
XINPUT_GAMEPAD_X = 0x4000
XINPUT_GAMEPAD_Y = 0x8000

# Maximum values for sticks and triggers
XINPUT_STICK_MAX = 32767
XINPUT_STICK_MIN = -32768
XINPUT_TRIGGER_MAX = 255

class XINPUT_GAMEPAD(Structure):
    """XInput gamepad structure"""
    _fields_ = [
        ('wButtons', c_ushort),
        ('bLeftTrigger', c_ubyte),
        ('bRightTrigger', c_ubyte),
        ('sThumbLX', c_short),
        ('sThumbLY', c_short),
        ('sThumbRX', c_short),
        ('sThumbRY', c_short),
    ]

class XINPUT_STATE(Structure):
    """XInput state structure"""
    _fields_ = [
        ('dwPacketNumber', wintypes.DWORD),
        ('Gamepad', XINPUT_GAMEPAD),
    ]

class XINPUT_VIBRATION(Structure):
    """XInput vibration structure"""
    _fields_ = [
        ('wLeftMotorSpeed', c_ushort),
        ('wRightMotorSpeed', c_ushort),
    ]

class XboxController:
    """Xbox Controller Simulator using XInput"""
    
    def __init__(self, controller_id: int = 0):
        """
        Initialize Xbox controller simulator
        
        Args:
            controller_id: Controller ID (0-3)
        """
        self.controller_id = controller_id
        self.xinput = None
        self.connected = False
        
        # Try to load XInput library
        try:
            # Try XInput 1.4 first (Windows 8+)
            self.xinput = ctypes.windll.xinput1_4
        except OSError:
            try:
                # Fallback to XInput 1.3 (Windows 7)
                self.xinput = ctypes.windll.xinput1_3
            except OSError:
                try:
                    # Last resort: XInput 9.1.0
                    self.xinput = ctypes.windll.xinput9_1_0
                except OSError:
                    logger.error("XInput library not found")
                    return
        
        if self.xinput:
            # Define function signatures
            self.xinput.XInputSetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_VIBRATION)]
            self.xinput.XInputSetState.restype = wintypes.DWORD
            
            self.xinput.XInputGetState.argtypes = [wintypes.DWORD, ctypes.POINTER(XINPUT_STATE)]
            self.xinput.XInputGetState.restype = wintypes.DWORD
            
            self.connected = True
            logger.info(f"XInput controller {controller_id} initialized")
            
        # Current state
        self.current_state = XINPUT_GAMEPAD()
        self.reset_state()
        
    def reset_state(self):
        """Reset controller to neutral state"""
        self.current_state.wButtons = 0
        self.current_state.bLeftTrigger = 0
        self.current_state.bRightTrigger = 0
        self.current_state.sThumbLX = 0
        self.current_state.sThumbLY = 0
        self.current_state.sThumbRX = 0
        self.current_state.sThumbRY = 0
        self.update_state()
        
    def update_state(self):
        """Send current state to the system"""
        if not self.connected:
            logger.warning("XInput controller not connected, cannot send input")
            return False
            
        try:
            # Note: XInput doesn't have a direct way to simulate input
            # This is a limitation - XInput is mainly for reading controller state
            # For actual input simulation, we might need to use other methods
            # like virtual controller drivers or DirectInput
            
            # Log the intended actions with more detail
            logger.info(f"XInput SIMULATION (not real): Buttons={self.current_state.wButtons:04X}, "
                       f"LT={self.current_state.bLeftTrigger}, RT={self.current_state.bRightTrigger}, "
                       f"LS=({self.current_state.sThumbLX}, {self.current_state.sThumbLY}), "
                       f"RS=({self.current_state.sThumbRX}, {self.current_state.sThumbRY})")
            
            # XInput cannot actually send input - this is just simulation
            logger.warning("XInput controller cannot send real input - falling back to keyboard emulator")
            return False  # Return False to indicate input wasn't actually sent
            
        except Exception as e:
            logger.error(f"Error updating controller state: {e}")
            return False
            
    def press_button(self, button: int, duration: float = 0.1):
        """
        Press a button for a specified duration
        
        Args:
            button: Button constant (e.g., XINPUT_GAMEPAD_A)
            duration: How long to hold the button in seconds
        """
        button_name = self.get_button_name(button)
        logger.info(f"XInput: Pressing {button_name} for {duration}s")
        
        self.current_state.wButtons |= button
        result = self.update_state()
        
        if duration > 0:
            time.sleep(duration)
            self.current_state.wButtons &= ~button
            self.update_state()
            
        return result
        
    def get_button_name(self, button: int) -> str:
        """Get human-readable button name"""
        button_names = {
            XINPUT_GAMEPAD_A: "A",
            XINPUT_GAMEPAD_B: "B", 
            XINPUT_GAMEPAD_X: "X",
            XINPUT_GAMEPAD_Y: "Y",
            XINPUT_GAMEPAD_START: "Start",
            XINPUT_GAMEPAD_BACK: "Back",
            XINPUT_GAMEPAD_DPAD_UP: "D-Up",
            XINPUT_GAMEPAD_DPAD_DOWN: "D-Down",
            XINPUT_GAMEPAD_DPAD_LEFT: "D-Left",
            XINPUT_GAMEPAD_DPAD_RIGHT: "D-Right",
            XINPUT_GAMEPAD_LEFT_SHOULDER: "LB",
            XINPUT_GAMEPAD_RIGHT_SHOULDER: "RB",
        }
        return button_names.get(button, f"Button_{button:04X}")
            
    def release_button(self, button: int):
        """Release a specific button"""
        self.current_state.wButtons &= ~button
        self.update_state()
        
    def set_trigger(self, trigger: str, value: float):
        """
        Set trigger value
        
        Args:
            trigger: 'left' or 'right'
            value: Trigger value (0.0 to 1.0)
        """
        trigger_value = int(max(0, min(255, value * 255)))
        
        if trigger.lower() == 'left':
            self.current_state.bLeftTrigger = trigger_value
        elif trigger.lower() == 'right':
            self.current_state.bRightTrigger = trigger_value
            
        self.update_state()
        
    def set_stick(self, stick: str, x: float, y: float):
        """
        Set stick position
        
        Args:
            stick: 'left' or 'right'
            x: X axis value (-1.0 to 1.0)
            y: Y axis value (-1.0 to 1.0)
        """
        x_value = int(max(XINPUT_STICK_MIN, min(XINPUT_STICK_MAX, x * XINPUT_STICK_MAX)))
        y_value = int(max(XINPUT_STICK_MIN, min(XINPUT_STICK_MAX, y * XINPUT_STICK_MAX)))
        
        if stick.lower() == 'left':
            self.current_state.sThumbLX = x_value
            self.current_state.sThumbLY = y_value
        elif stick.lower() == 'right':
            self.current_state.sThumbRX = x_value
            self.current_state.sThumbRY = y_value
            
        self.update_state()
        
    def move_stick_random(self, stick: str, intensity: float = 0.5, duration: float = 1.0):
        """
        Move stick in random direction
        
        Args:
            stick: 'left' or 'right'
            intensity: Movement intensity (0.0 to 1.0)
            duration: How long to hold the movement
        """
        angle = random.uniform(0, 2 * 3.14159)
        x = intensity * random.uniform(0.3, 1.0) * math.cos(angle)
        y = intensity * random.uniform(0.3, 1.0) * math.sin(angle)
        
        self.set_stick(stick, x, y)
        time.sleep(duration)
        self.set_stick(stick, 0, 0)
        
    # Convenience methods for common actions
    def press_a(self, duration: float = 0.1):
        """Press A button"""
        self.press_button(XINPUT_GAMEPAD_A, duration)
        
    def press_b(self, duration: float = 0.1):
        """Press B button"""
        self.press_button(XINPUT_GAMEPAD_B, duration)
        
    def press_x(self, duration: float = 0.1):
        """Press X button"""
        self.press_button(XINPUT_GAMEPAD_X, duration)
        
    def press_y(self, duration: float = 0.1):
        """Press Y button"""
        self.press_button(XINPUT_GAMEPAD_Y, duration)
        
    def press_start(self, duration: float = 0.1):
        """Press Start button"""
        self.press_button(XINPUT_GAMEPAD_START, duration)
        
    def press_back(self, duration: float = 0.1):
        """Press Back/Select button"""
        self.press_button(XINPUT_GAMEPAD_BACK, duration)
        
    def press_dpad_up(self, duration: float = 0.1):
        """Press D-pad up"""
        self.press_button(XINPUT_GAMEPAD_DPAD_UP, duration)
        
    def press_dpad_down(self, duration: float = 0.1):
        """Press D-pad down"""
        self.press_button(XINPUT_GAMEPAD_DPAD_DOWN, duration)
        
    def press_dpad_left(self, duration: float = 0.1):
        """Press D-pad left"""
        self.press_button(XINPUT_GAMEPAD_DPAD_LEFT, duration)
        
    def press_dpad_right(self, duration: float = 0.1):
        """Press D-pad right"""
        self.press_button(XINPUT_GAMEPAD_DPAD_RIGHT, duration)
        
    def press_left_bumper(self, duration: float = 0.1):
        """Press left bumper"""
        self.press_button(XINPUT_GAMEPAD_LEFT_SHOULDER, duration)
        
    def press_right_bumper(self, duration: float = 0.1):
        """Press right bumper"""
        self.press_button(XINPUT_GAMEPAD_RIGHT_SHOULDER, duration)
        
    def press_left_stick(self, duration: float = 0.1):
        """Press left stick button"""
        self.press_button(XINPUT_GAMEPAD_LEFT_THUMB, duration)
        
    def press_right_stick(self, duration: float = 0.1):
        """Press right stick button"""
        self.press_button(XINPUT_GAMEPAD_RIGHT_THUMB, duration)

# Alternative implementation using keyboard simulation
# This is a fallback for when XInput simulation doesn't work
import pyautogui

class KeyboardXboxEmulator:
    """
    Xbox controller emulator using keyboard inputs
    Maps Xbox controller buttons to keyboard keys
    """
    
    def __init__(self):
        """Initialize keyboard emulator with default key mappings"""
        self.key_mapping = {
            'a': 'space',           # A button -> Space
            'b': 'esc',             # B button -> Escape
            'x': 'f',               # X button -> F
            'y': 'r',               # Y button -> R
            'start': 'enter',       # Start -> Enter
            'back': 'backspace',    # Back -> Backspace
            'dpad_up': 'up',        # D-pad up -> Arrow up
            'dpad_down': 'down',    # D-pad down -> Arrow down
            'dpad_left': 'left',    # D-pad left -> Arrow left
            'dpad_right': 'right',  # D-pad right -> Arrow right
            'left_bumper': 'q',     # Left bumper -> Q
            'right_bumper': 'e',    # Right bumper -> E
            'left_trigger': 'shift', # Left trigger -> Shift
            'right_trigger': 'ctrl', # Right trigger -> Ctrl
            'left_stick_x': ['a', 'd'],   # Left stick X -> A/D
            'left_stick_y': ['w', 's'],   # Left stick Y -> W/S
            'right_stick_x': ['j', 'l'],  # Right stick X -> J/L
            'right_stick_y': ['i', 'k'],  # Right stick Y -> I/K
        }
        
        logger.info("Keyboard Xbox emulator initialized")
        
    def press_button(self, button: str, duration: float = 0.1):
        """Press a button using keyboard simulation"""
        if button in self.key_mapping:
            key = self.key_mapping[button]
            logger.info(f"Keyboard Emulator: Pressing {button} -> {key} for {duration}s")
            
            try:
                pyautogui.keyDown(key)
                time.sleep(duration)
                pyautogui.keyUp(key)
                logger.info(f"Successfully pressed {button} -> {key}")
                return True
            except Exception as e:
                logger.error(f"Failed to press {button} -> {key}: {e}")
                return False
        else:
            logger.warning(f"Button {button} not mapped in keyboard emulator")
            return False
            
    def test_input(self) -> bool:
        """Test if keyboard input is working"""
        try:
            logger.info("Testing keyboard emulator...")
            # Try a simple key press test
            pyautogui.press('f1')  # F1 is usually safe to test
            logger.info("Keyboard emulator test successful")
            return True
        except Exception as e:
            logger.error(f"Keyboard emulator test failed: {e}")
            return False
            
    def move_stick(self, stick: str, direction: str, duration: float = 0.5):
        """Simulate stick movement using keyboard keys"""
        if stick == 'left':
            if direction == 'up':
                pyautogui.keyDown('w')
                time.sleep(duration)
                pyautogui.keyUp('w')
            elif direction == 'down':
                pyautogui.keyDown('s')
                time.sleep(duration)
                pyautogui.keyUp('s')
            elif direction == 'left':
                pyautogui.keyDown('a')
                time.sleep(duration)
                pyautogui.keyUp('a')
            elif direction == 'right':
                pyautogui.keyDown('d')
                time.sleep(duration)
                pyautogui.keyUp('d')
                
    def simulate_random_movement(self, duration: float = 2.0):
        """Simulate random movement to stay active"""
        movements = ['w', 'a', 's', 'd']
        
        start_time = time.time()
        while time.time() - start_time < duration:
            # Random movement
            key = random.choice(movements)
            pyautogui.keyDown(key)
            time.sleep(random.uniform(0.1, 0.8))
            pyautogui.keyUp(key)
            
            # Random pause
            time.sleep(random.uniform(0.1, 0.5))
            
            # Occasional jump
            if random.random() < 0.3:
                pyautogui.press('space')
                
    # Convenience methods
    def press_a(self, duration: float = 0.1):
        self.press_button('a', duration)
        
    def press_b(self, duration: float = 0.1):
        self.press_button('b', duration)
        
    def press_x(self, duration: float = 0.1):
        self.press_button('x', duration)
        
    def press_y(self, duration: float = 0.1):
        self.press_button('y', duration)
        
    def press_start(self, duration: float = 0.1):
        self.press_button('start', duration)

# Import math for stick calculations
import math

def create_controller(use_xinput: bool = True) -> object:
    """
    Create a controller instance
    
    Args:
        use_xinput: Whether to try XInput first, fallback to keyboard if failed
        
    Returns:
        Controller instance
    """
    logger.info("Creating controller instance...")
    
    if use_xinput:
        try:
            logger.info("Attempting to create XInput controller...")
            controller = XboxController()
            if controller.connected:
                logger.warning("XInput controller created but cannot send real input")
                logger.info("Falling back to keyboard emulator for actual input")
                # Always fall back to keyboard since XInput can't send input
            else:
                logger.warning("XInput controller failed to connect")
        except Exception as e:
            logger.warning(f"XInput controller failed: {e}")
            
    logger.info("Using keyboard emulator for controller simulation")
    keyboard_controller = KeyboardXboxEmulator()
    
    # Test the keyboard controller
    if keyboard_controller.test_input():
        logger.info("Keyboard controller ready and tested")
    else:
        logger.error("Keyboard controller test failed - inputs may not work")
        
    return keyboard_controller