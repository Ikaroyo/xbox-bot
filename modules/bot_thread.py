"""
Bot Thread Module

Main bot logic that runs in a separate thread to avoid blocking the GUI.
Handles the main detection and action loop with configurable rules.
"""

import threading
import time
from typing import List, Dict, Callable, Optional
from .window_manager import WindowManager
from .image_detector import ImageDetector
from .virtual_controller import VirtualController, XboxButton, InputMode


class BotThread(threading.Thread):
    """Main bot thread that handles detection and action execution."""
    
    def __init__(self, 
                 window_manager: WindowManager,
                 image_detector: ImageDetector,
                 virtual_controller: VirtualController,
                 log_callback: Callable[[str], None] = None,
                 config_manager = None):
        """
        Initialize the bot thread.
        
        Args:
            window_manager: WindowManager instance
            image_detector: ImageDetector instance
            virtual_controller: VirtualController instance
            log_callback: Function to call for logging messages
        """
        super().__init__(daemon=True)
        
        self.window_manager = window_manager
        self.image_detector = image_detector
        self.virtual_controller = virtual_controller
        self.log_callback = log_callback
        self.config_manager = config_manager
        
        # Bot state
        self.running = False
        self.paused = False
        self.rules = []
        
        # Configuration
        self.loop_delay = 0.1  # Delay between detection cycles (seconds)
        self.action_cooldown = 1.0  # Cooldown after successful action (seconds)
        self.window_title = "Xbox"
        self.target_window_size = (1280, 720)
        self.debug_save_screenshots = False  # Save screenshots for debugging
        
        # Internal state
        self._stop_event = threading.Event()
        self._last_action_time = 0
        self._current_window = None
    
    def log(self, message: str):
        """Log a message using the callback if available."""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
    
    def set_rules(self, rules: List[Dict]):
        """
        Set the detection rules for the bot.
        
        Args:
            rules: List of rule dictionaries containing:
                - name: Rule identifier
                - template: Template image name
                - confidence: Minimum confidence threshold
                - action: Controller action to perform
        """
        self.rules = rules.copy()
        self.log(f"Updated bot rules: {len(self.rules)} rules loaded")
        
        # Debug: Log each rule received
        if len(self.rules) > 0:
            self.log("DEBUG: Rules received by bot thread:")
            for i, rule in enumerate(self.rules):
                self.log(f"  Rule {i+1}: {rule.get('name', 'Unknown')} - {rule.get('template', 'No template')} -> {rule.get('action', 'No action')}")
        else:
            self.log("DEBUG: No rules received by bot thread")
    
    def set_window_config(self, window_title: str, target_size: tuple):
        """
        Set window configuration.
        
        Args:
            window_title: Title of the target window
            target_size: (width, height) tuple for window resizing
        """
        self.window_title = window_title
        self.target_window_size = target_size
        self.log(f"Window config updated: '{window_title}' -> {target_size}")
    
    def set_timing_config(self, loop_delay: float, action_cooldown: float):
        """
        Set timing configuration.
        
        Args:
            loop_delay: Delay between detection cycles
            action_cooldown: Cooldown after successful actions
        """
        self.loop_delay = max(0.01, loop_delay)
        self.action_cooldown = max(0.1, action_cooldown)
        self.log(f"Timing config updated: loop={self.loop_delay}s, cooldown={self.action_cooldown}s")
    
    def start_bot(self):
        """Start the bot if not already running."""
        if not self.running:
            self.running = True
            self.paused = False
            self._stop_event.clear()
            
            if not self.is_alive():
                # Start new thread - DO NOT reinitialize, just start the thread
                super().__init__(daemon=True)
                self.running = True  # Ensure this is set after thread init
                self.start()
            
            self.log("Bot started")
    
    def stop_bot(self):
        """Stop the bot."""
        self.running = False
        self._stop_event.set()
        self.log("Bot stop requested")
    
    def pause_bot(self):
        """Pause the bot without stopping the thread."""
        self.paused = True
        self.log("Bot paused")
    
    def resume_bot(self):
        """Resume the bot if paused."""
        self.paused = False
        self.log("Bot resumed")
    
    def is_running(self) -> bool:
        """Check if the bot is currently running."""
        return self.running and not self.paused
    
    def _setup_window(self) -> bool:
        """
        Setup the target window for capture.
        
        Returns:
            True if window setup successful, False otherwise
        """
        try:
            # Find the window
            windows = self.window_manager.find_windows_by_title(self.window_title)
            
            if not windows:
                self.log(f"No windows found with title '{self.window_title}'")
                return False
            
            if len(windows) > 1:
                self.log(f"Multiple windows found with title '{self.window_title}'. Using first one.")
                for i, window in enumerate(windows):
                    self.log(f"  {i+1}. PID: {window['pid']}, Process: {window['process_name']}")
            
            # Use the first window found
            window = windows[0]
            self._current_window = window
            
            # Focus the window
            if not self.window_manager.focus_window(window):
                self.log("Failed to focus window")
                return False
            
            # Resize the window if needed
            width, height = self.target_window_size
            if not self.window_manager.resize_window(width, height, window):
                self.log(f"Failed to resize window to {width}x{height}")
                # Don't return False here - resizing might fail but capture could still work
            
            self.log(f"Window setup complete: {window['process_name']} (PID: {window['pid']})")
            return True
            
        except Exception as e:
            self.log(f"Error setting up window: {e}")
            return False
    
    def _capture_screen(self) -> Optional[object]:
        """
        Capture the current game window.
        
        Returns:
            Screenshot array or None if failed
        """
        try:
            if not self._current_window:
                return None
            
            # Check if window is still valid
            if not self.window_manager.is_window_valid(self._current_window):
                self.log("Current window is no longer valid")
                self._current_window = None
                return None
            
            # Get window capture area
            capture_area = self.window_manager.capture_window_area(self._current_window)
            if not capture_area:
                self.log("Failed to get window capture area")
                return None
            
            # Capture screenshot
            screenshot = self.image_detector.capture_screenshot(capture_area)
            if screenshot is None:
                self.log("Failed to capture screenshot")
            
            return screenshot
            
        except Exception as e:
            self.log(f"Error capturing screen: {e}")
            return None
    
    def _process_rules(self, screenshot) -> bool:
        """
        Process detection rules against the screenshot.
        
        Args:
            screenshot: Screenshot to analyze
            
        Returns:
            True if an action was executed, False otherwise
        """
        try:
            if len(self.rules) == 0:
                # Only log this once
                if not hasattr(self, '_no_rules_logged'):
                    self.log("DEBUG: No detection rules configured in bot thread")
                    self.log(f"DEBUG: self.rules length: {len(self.rules)}")
                    self.log(f"DEBUG: self.rules content: {self.rules}")
                    self._no_rules_logged = True
                return False
            
            for rule in self.rules:
                if not self.running or self.paused:
                    return False
                
                rule_name = rule.get('name', 'Unknown')
                template_name = rule.get('template')
                confidence = rule.get('confidence', 0.8)
                action = rule.get('action')
                
                if not template_name or not action:
                    if not hasattr(self, '_invalid_rules_logged'):
                        self.log(f"Invalid rule: {rule_name} - missing template or action")
                        self._invalid_rules_logged = True
                    continue
                
                # Try to find the template
                match = self.image_detector.find_template(screenshot, template_name, confidence)
                
                if match:
                    self.log(f"Detected: {rule_name} (confidence: {match['confidence']:.3f})")
                    
                    # Handle cycle tracking if enabled
                    self._handle_cycle_tracking(rule)
                    
                    # Execute the action
                    if self._execute_action(action, rule_name):
                        # Action executed successfully, apply cooldown
                        self._last_action_time = time.time()
                        return True
                    else:
                        self.log(f"Failed to execute action for rule: {rule_name}")
                else:
                    # Log template not found periodically for debugging
                    if not hasattr(self, '_template_miss_count'):
                        self._template_miss_count = {}
                    
                    if template_name not in self._template_miss_count:
                        self._template_miss_count[template_name] = 0
                    
                    self._template_miss_count[template_name] += 1
                    
                    # Log every 100 misses with more debug info
                    if self._template_miss_count[template_name] % 100 == 1:
                        self.log(f"Template '{template_name}' not found (searched {self._template_miss_count[template_name]} times)")
                        self.log(f"  - Screenshot size: {screenshot.shape if screenshot is not None else 'None'}")
                        self.log(f"  - Confidence threshold: {confidence}")
                        
                        # Save debug screenshot if enabled
                        if self.debug_save_screenshots and screenshot is not None:
                            self._save_debug_screenshot(screenshot, template_name, self._template_miss_count[template_name])
            
            return False
            
        except Exception as e:
            self.log(f"Error processing rules: {e}")
            return False
    
    def _execute_action(self, action: str, rule_name: str) -> bool:
        """
        Execute a controller action (single button or sequence).
        
        Args:
            action: Action string (button name or sequence)
            rule_name: Name of the rule for logging
            
        Returns:
            True if action executed successfully, False otherwise
        """
        try:
            # Check if this is a sequence (contains comma and colon)
            if ',' in action and ':' in action:
                # Execute sequence
                success = self.virtual_controller.execute_sequence(action)
                if success:
                    self.log(f"Sequence executed: {action} (rule: {rule_name})")
                else:
                    self.log(f"Failed to execute sequence: {action}")
                return success
            else:
                # Single button press
                button = self.virtual_controller.get_button_from_string(action)
                
                if button is None:
                    self.log(f"Unknown action '{action}' for rule: {rule_name}")
                    return False
                
                # Execute the button press
                success = self.virtual_controller.press_button(button)
                
                if success:
                    self.log(f"Action executed: {action} (rule: {rule_name})")
                else:
                    self.log(f"Failed to execute action: {action}")
                
                return success
            
        except Exception as e:
            self.log(f"Error executing action '{action}': {e}")
            return False
    
    def _is_cooldown_active(self) -> bool:
        """Check if action cooldown is still active."""
        return time.time() - self._last_action_time < self.action_cooldown
    
    def _save_debug_screenshot(self, screenshot, template_name: str, miss_count: int):
        """Save a debug screenshot for analysis."""
        try:
            import cv2
            import os
            from datetime import datetime
            
            debug_dir = "debug_screenshots"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug_{template_name}_{miss_count}_{timestamp}.png"
            filepath = os.path.join(debug_dir, filename)
            
            cv2.imwrite(filepath, screenshot)
            self.log(f"Debug screenshot saved: {filepath}")
            
        except Exception as e:
            self.log(f"Error saving debug screenshot: {e}")
    
    def enable_debug_screenshots(self, enabled: bool = True):
        """Enable or disable debug screenshot saving."""
        self.debug_save_screenshots = enabled
        self.log(f"Debug screenshots {'enabled' if enabled else 'disabled'}")
    
    def run(self):
        """Main bot loop that runs in the thread."""
        self.log("Bot thread started")
        
        try:
            while self.running and not self._stop_event.is_set():
                # Check if paused
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                # Check if cooldown is active
                if self._is_cooldown_active():
                    time.sleep(0.1)
                    continue
                
                # Setup window if not already done
                if not self._current_window:
                    if not self._setup_window():
                        self.log("Retrying window setup in 2 seconds...")
                        time.sleep(2.0)
                        continue
                
                # Capture screenshot
                screenshot = self._capture_screen()
                if screenshot is None:
                    # Try to re-setup window
                    self._current_window = None
                    time.sleep(1.0)
                    continue
                
                # Process detection rules
                action_executed = self._process_rules(screenshot)
                
                # Log periodic status if no action executed
                if not action_executed and len(self.rules) > 0:
                    # Log every 30 cycles (approximately every 3 seconds at 0.1 delay)
                    if not hasattr(self, '_cycle_count'):
                        self._cycle_count = 0
                    self._cycle_count += 1
                    
                    if self._cycle_count % 30 == 0:
                        self.log(f"Scanning... ({len(self.rules)} rules active, cycle {self._cycle_count})")
                
                # Sleep before next iteration
                time.sleep(self.loop_delay)
                
        except Exception as e:
            self.log(f"Fatal error in bot thread: {e}")
        
        finally:
            self.running = False
            self.log("Bot thread stopped")
    
    def get_status(self) -> Dict:
        """
        Get current bot status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            'running': self.running,
            'paused': self.paused,
            'rules_count': len(self.rules),
            'window_title': self.window_title,
            'current_window': self._current_window is not None,
            'cooldown_active': self._is_cooldown_active(),
            'controller_connected': self.virtual_controller.is_connected()
        }
    
    def _handle_cycle_tracking(self, rule: Dict):
        """Handle cycle tracking when a rule is triggered."""
        try:
            # Only process if config manager is available and rule has cycle tracking
            if not self.config_manager or not rule.get('is_cycle_marker', False):
                return
            
            cycle_name = rule.get('cycle_name', '')
            cycle_type = rule.get('cycle_type', 'none')
            rule_name = rule.get('name', 'Unknown')
            
            if not cycle_name or cycle_type == 'none':
                return
            
            if cycle_type == 'start':
                # Check for duplicate cycle start
                if self.config_manager.is_cycle_duplicate(cycle_name):
                    self.log(f"🔄 Ignoring duplicate cycle start for '{cycle_name}'")
                    return
                
                # Start new cycle
                if self.config_manager.start_cycle(cycle_name, rule_name):
                    self.log(f"🎯 Started cycle: '{cycle_name}' with rule '{rule_name}'")
                    
            elif cycle_type == 'checkpoint':
                # Add checkpoint to active cycle
                if self.config_manager.add_cycle_checkpoint(cycle_name, rule_name):
                    self.log(f"📍 Checkpoint: '{rule_name}' in cycle '{cycle_name}'")
                    
            elif cycle_type == 'end':
                # End cycle and get statistics
                stats = self.config_manager.end_cycle(cycle_name, rule_name)
                if stats:
                    duration = stats.get('duration', 0)
                    checkpoint_count = stats.get('checkpoint_count', 0)
                    self.log(f"🏁 Completed cycle: '{cycle_name}' in {duration:.1f}s ({checkpoint_count} checkpoints)")
                    
                    # Check against expected time if specified
                    expected_time = rule.get('expected_cycle_time', 0)
                    if expected_time > 0:
                        tolerance = rule.get('cycle_tolerance', 0.3)
                        time_diff = abs(duration - expected_time)
                        time_ratio = time_diff / expected_time
                        
                        if time_ratio <= tolerance:
                            self.log(f"✅ Cycle time within expected range ({expected_time:.1f}s ±{tolerance*100:.0f}%)")
                        else:
                            status = "faster" if duration < expected_time else "slower"
                            self.log(f"⚠️ Cycle {status} than expected: {duration:.1f}s vs {expected_time:.1f}s")
                    
                    # Show cycle statistics
                    cycle_stats = self.config_manager.get_cycle_statistics(cycle_name)
                    if cycle_stats:
                        total_cycles = cycle_stats.get('total_cycles', 0)
                        avg_time = cycle_stats.get('average_time', 0)
                        self.log(f"📊 Total cycles: {total_cycles}, Average: {avg_time:.1f}s")
                
                # Clean up old cycles periodically
                if stats and stats.get('duration', 0) > 0:
                    self.config_manager.cleanup_old_cycles()
                    
        except Exception as e:
            self.log(f"Error in cycle tracking: {e}")