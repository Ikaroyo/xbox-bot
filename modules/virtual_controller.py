"""
Virtual Controller Module

Wrapper for vgamepad to simulate Xbox 360 controller input.
Provides simplified methods for button presses and joystick movements.
"""

import vgamepad as vg
import time
from typing import Optional
from enum import Enum


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
    """Handles Xbox 360 controller simulation using vgamepad."""
    
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