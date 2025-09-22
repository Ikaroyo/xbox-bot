"""
Image Recognition System
Provides template matching and game state detection using OpenCV
"""

import cv2
import numpy as np
import pyautogui
import pygetwindow
from PIL import Image
import time
import os
from typing import Dict, List, Tuple, Optional, NamedTuple
import logging

logger = logging.getLogger(__name__)

class MatchResult(NamedTuple):
    """Result of template matching"""
    found: bool
    confidence: float
    position: Tuple[int, int]
    center: Tuple[int, int]
    template_size: Tuple[int, int]

class ImageRecognizer:
    """
    Image recognition system for game state detection
    """
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize image recognizer
        
        Args:
            templates_dir: Directory containing template images
        """
        self.templates_dir = templates_dir
        self.templates_cache = {}
        self.screenshot_cache = None
        self.screenshot_timestamp = 0
        self.cache_duration = 0.5  # Cache screenshots for 0.5 seconds
        
        # Create templates directory if it doesn't exist
        os.makedirs(templates_dir, exist_ok=True)
        
        logger.info("Image recognizer initialized")
        
    def load_template(self, template_path: str) -> Optional[np.ndarray]:
        """
        Load and cache a template image
        
        Args:
            template_path: Path to template image
            
        Returns:
            Template image as numpy array or None if failed
        """
        try:
            # Check cache first
            if template_path in self.templates_cache:
                return self.templates_cache[template_path]
                
            # Load template
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"Could not load template: {template_path}")
                return None
                
            # Cache template
            self.templates_cache[template_path] = template
            logger.debug(f"Loaded template: {template_path}")
            
            return template
            
        except Exception as e:
            logger.error(f"Error loading template {template_path}: {e}")
            return None
            
    def get_screenshot(self, window=None, force_refresh: bool = False) -> Optional[np.ndarray]:
        """
        Get screenshot of the game window or entire screen
        
        Args:
            window: PyGetWindow window object (if None, captures entire screen)
            force_refresh: Force new screenshot even if cached
            
        Returns:
            Screenshot as OpenCV image or None if failed
        """
        try:
            current_time = time.time()
            
            # Return cached screenshot if recent and not forced refresh
            if (not force_refresh and 
                self.screenshot_cache is not None and 
                current_time - self.screenshot_timestamp < self.cache_duration):
                return self.screenshot_cache
                
            # Take new screenshot
            if window and hasattr(window, 'left'):
                # Capture specific window
                screenshot = pyautogui.screenshot(region=(
                    window.left, window.top, window.width, window.height
                ))
            else:
                # Capture entire screen
                screenshot = pyautogui.screenshot()
                
            # Convert PIL to OpenCV format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Cache screenshot
            self.screenshot_cache = screenshot_cv
            self.screenshot_timestamp = current_time
            
            return screenshot_cv
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
            
    def find_template(self, template_path: str, screenshot: Optional[np.ndarray] = None, 
                     confidence_threshold: float = 0.8, method: int = cv2.TM_CCOEFF_NORMED) -> MatchResult:
        """
        Find template in screenshot using template matching
        
        Args:
            template_path: Path to template image
            screenshot: Screenshot to search in (if None, takes new screenshot)
            confidence_threshold: Minimum confidence for match
            method: OpenCV template matching method
            
        Returns:
            MatchResult with detection information
        """
        try:
            # Load template
            template = self.load_template(template_path)
            if template is None:
                return MatchResult(False, 0.0, (0, 0), (0, 0), (0, 0))
                
            # Get screenshot if not provided
            if screenshot is None:
                screenshot = self.get_screenshot()
                if screenshot is None:
                    return MatchResult(False, 0.0, (0, 0), (0, 0), (0, 0))
                    
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Get template dimensions
            template_height, template_width = template.shape[:2]
            
            # Determine if match is good enough
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                # For these methods, lower values are better
                confidence = 1.0 - min_val
                match_loc = min_loc
            else:
                # For other methods, higher values are better
                confidence = max_val
                match_loc = max_loc
                
            found = confidence >= confidence_threshold
            
            # Calculate center position
            center_x = match_loc[0] + template_width // 2
            center_y = match_loc[1] + template_height // 2
            
            return MatchResult(
                found=found,
                confidence=confidence,
                position=match_loc,
                center=(center_x, center_y),
                template_size=(template_width, template_height)
            )
            
        except Exception as e:
            logger.error(f"Error finding template {template_path}: {e}")
            return MatchResult(False, 0.0, (0, 0), (0, 0), (0, 0))
            
    def find_multiple_templates(self, template_configs: Dict[str, Dict], 
                               screenshot: Optional[np.ndarray] = None) -> Dict[str, MatchResult]:
        """
        Find multiple templates in a single screenshot
        
        Args:
            template_configs: Dict with template names as keys and config dicts as values
                            Config should contain 'path' and optionally 'confidence'
            screenshot: Screenshot to search in
            
        Returns:
            Dict with template names as keys and MatchResult as values
        """
        results = {}
        
        # Get screenshot once for all templates
        if screenshot is None:
            screenshot = self.get_screenshot()
            if screenshot is None:
                return {name: MatchResult(False, 0.0, (0, 0), (0, 0), (0, 0)) 
                       for name in template_configs.keys()}
                
        # Find each template
        for name, config in template_configs.items():
            template_path = config.get('path', '')
            confidence = config.get('confidence', 0.8)
            
            result = self.find_template(template_path, screenshot, confidence)
            results[name] = result
            
            if result.found:
                logger.debug(f"Found template '{name}' with confidence {result.confidence:.3f}")
                
        return results
        
    def capture_template_around_cursor(self, capture_size: int = 100, 
                                     save_path: Optional[str] = None) -> Optional[str]:
        """
        Capture a template image around the current cursor position
        
        Args:
            capture_size: Size of the square area to capture
            save_path: Path to save the template (if None, generates path)
            
        Returns:
            Path to saved template or None if failed
        """
        try:
            # Get cursor position
            cursor_x, cursor_y = pyautogui.position()
            
            # Calculate capture region
            left = max(0, cursor_x - capture_size // 2)
            top = max(0, cursor_y - capture_size // 2)
            
            # Capture screenshot
            screenshot = pyautogui.screenshot(region=(left, top, capture_size, capture_size))
            
            # Generate save path if not provided
            if save_path is None:
                timestamp = int(time.time())
                save_path = os.path.join(self.templates_dir, f"template_{timestamp}.png")
                
            # Save template
            screenshot.save(save_path)
            logger.info(f"Template captured and saved to: {save_path}")
            
            return save_path
            
        except Exception as e:
            logger.error(f"Error capturing template: {e}")
            return None
            
    def draw_matches_on_screenshot(self, screenshot: np.ndarray, 
                                  matches: Dict[str, MatchResult]) -> np.ndarray:
        """
        Draw bounding boxes around matched templates on screenshot
        
        Args:
            screenshot: Screenshot image
            matches: Dictionary of match results
            
        Returns:
            Screenshot with drawn matches
        """
        result_image = screenshot.copy()
        
        for name, match in matches.items():
            if match.found:
                # Draw rectangle around match
                top_left = match.position
                bottom_right = (
                    top_left[0] + match.template_size[0],
                    top_left[1] + match.template_size[1]
                )
                
                # Draw bounding box
                cv2.rectangle(result_image, top_left, bottom_right, (0, 255, 0), 2)
                
                # Draw center point
                cv2.circle(result_image, match.center, 5, (0, 0, 255), -1)
                
                # Draw label
                label = f"{name}: {match.confidence:.2f}"
                cv2.putText(result_image, label, 
                           (top_left[0], top_left[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                           
        return result_image
        
    def save_debug_image(self, screenshot: np.ndarray, matches: Dict[str, MatchResult], 
                        filename: Optional[str] = None) -> str:
        """
        Save a debug image with match visualization
        
        Args:
            screenshot: Screenshot image
            matches: Dictionary of match results
            filename: Output filename (if None, generates timestamp-based name)
            
        Returns:
            Path to saved debug image
        """
        if filename is None:
            timestamp = int(time.time())
            filename = f"debug_{timestamp}.png"
            
        debug_image = self.draw_matches_on_screenshot(screenshot, matches)
        cv2.imwrite(filename, debug_image)
        
        logger.info(f"Debug image saved: {filename}")
        return filename
        
    def clear_cache(self):
        """Clear screenshot cache"""
        self.screenshot_cache = None
        self.screenshot_timestamp = 0
        
    def clear_template_cache(self):
        """Clear template cache"""
        self.templates_cache.clear()

class GameStateDetector:
    """
    High-level game state detection using image recognition
    """
    
    def __init__(self, recognizer: ImageRecognizer, config: Dict):
        """
        Initialize game state detector
        
        Args:
            recognizer: ImageRecognizer instance
            config: Configuration with template definitions
        """
        self.recognizer = recognizer
        self.config = config
        self.last_state = "unknown"
        self.state_history = []
        self.max_history = 10
        
    def detect_current_state(self, window=None) -> Tuple[str, Dict[str, MatchResult]]:
        """
        Detect the current game state
        
        Args:
            window: Game window object
            
        Returns:
            Tuple of (state_name, match_results)
        """
        try:
            # Get current screenshot
            screenshot = self.recognizer.get_screenshot(window)
            if screenshot is None:
                return "error", {}
                
            # Get template configurations
            templates = self.config.get('templates', {})
            if not templates:
                return "no_templates", {}
                
            # Find all templates
            matches = self.recognizer.find_multiple_templates(templates, screenshot)
            
            # Determine state based on matches
            state = self._determine_state_from_matches(matches)
            
            # Update state history
            self._update_state_history(state)
            
            logger.debug(f"Detected state: {state}")
            return state, matches
            
        except Exception as e:
            logger.error(f"Error detecting game state: {e}")
            return "error", {}
            
    def _determine_state_from_matches(self, matches: Dict[str, MatchResult]) -> str:
        """
        Determine game state based on template matches
        
        Args:
            matches: Dictionary of match results
            
        Returns:
            State name
        """
        # Priority order for state detection
        state_priority = [
            'game_lost',
            'get_reward', 
            'main_menu',
            'game_results',
            'game_running'
        ]
        
        # Check each state in priority order
        for state in state_priority:
            if state in matches and matches[state].found:
                return state
                
        # If no specific state detected, check if any template was found
        any_found = any(match.found for match in matches.values())
        
        if any_found:
            return "unknown_state"
        else:
            return "no_match"
            
    def _update_state_history(self, state: str):
        """Update state history for stability checking"""
        self.state_history.append(state)
        
        # Keep only recent history
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
            
        self.last_state = state
        
    def get_stable_state(self, min_occurrences: int = 2) -> str:
        """
        Get stable state that has occurred multiple times recently
        
        Args:
            min_occurrences: Minimum number of recent occurrences
            
        Returns:
            Stable state name
        """
        if len(self.state_history) < min_occurrences:
            return self.last_state
            
        # Check last few states
        recent_states = self.state_history[-min_occurrences:]
        
        # If all recent states are the same, it's stable
        if len(set(recent_states)) == 1:
            return recent_states[0]
            
        # Otherwise return the last state
        return self.last_state
        
    def is_state_stable(self, target_state: str, min_occurrences: int = 2) -> bool:
        """
        Check if a specific state has been stable recently
        
        Args:
            target_state: State to check for
            min_occurrences: Minimum consecutive occurrences
            
        Returns:
            True if state is stable
        """
        if len(self.state_history) < min_occurrences:
            return False
            
        recent_states = self.state_history[-min_occurrences:]
        return all(state == target_state for state in recent_states)