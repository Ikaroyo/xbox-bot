"""
Image Detector Module

Handles template matching using OpenCV for game state detection.
Provides functions to capture screenshots and find template images.
"""

import cv2
import numpy as np
from PIL import Image, ImageGrab
import os
from typing import Optional, Tuple, List, Dict


class ImageDetector:
    """Handles image template matching and screenshot operations."""
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize the ImageDetector.
        
        Args:
            templates_dir: Directory where template images are stored
        """
        self.templates_dir = templates_dir
        self.templates_cache = {}
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
    
    def capture_screenshot(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Capture a screenshot of the screen or specified area.
        
        Args:
            bbox: Bounding box as (x, y, width, height). If None, captures full screen.
            
        Returns:
            Screenshot as numpy array in BGR format, or None if failed
        """
        try:
            if bbox:
                x, y, width, height = bbox
                screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            else:
                screenshot = ImageGrab.grab()
            
            # Convert PIL image to OpenCV format (BGR)
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            return screenshot_bgr
            
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
    
    def capture_area_around_cursor(self, cursor_pos: Tuple[int, int], 
                                 area_size: Tuple[int, int]) -> Optional[np.ndarray]:
        """
        Capture a rectangular area around the cursor position.
        
        Args:
            cursor_pos: (x, y) position of the cursor
            area_size: (width, height) of the area to capture
            
        Returns:
            Screenshot as numpy array in BGR format, or None if failed
        """
        try:
            cursor_x, cursor_y = cursor_pos
            width, height = area_size
            
            # Calculate capture area centered on cursor
            x = cursor_x - width // 2
            y = cursor_y - height // 2
            
            # Ensure we don't go outside screen bounds
            x = max(0, x)
            y = max(0, y)
            
            return self.capture_screenshot((x, y, width, height))
            
        except Exception as e:
            print(f"Error capturing area around cursor: {e}")
            return None
    
    def save_template(self, image: np.ndarray, name: str) -> bool:
        """
        Save an image as a template file.
        
        Args:
            image: Image array in BGR format
            name: Name for the template (without extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template_path = os.path.join(self.templates_dir, f"{name}.png")
            success = cv2.imwrite(template_path, image)
            
            if success:
                # Clear cache for this template
                if name in self.templates_cache:
                    del self.templates_cache[name]
                    
            return success
            
        except Exception as e:
            print(f"Error saving template '{name}': {e}")
            return False
    
    def load_template(self, name: str) -> Optional[np.ndarray]:
        """
        Load a template image from file, with caching.
        
        Args:
            name: Name of the template (with or without .png extension)
            
        Returns:
            Template image as numpy array in BGR format, or None if not found
        """
        # Normalize name - remove .png if present
        clean_name = name[:-4] if name.endswith('.png') else name
        
        # Check cache first
        if clean_name in self.templates_cache:
            return self.templates_cache[clean_name]
        
        try:
            template_path = os.path.join(self.templates_dir, f"{clean_name}.png")
            
            if not os.path.exists(template_path):
                return None
            
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if template is not None:
                self.templates_cache[clean_name] = template
                
            return template
            
        except Exception as e:
            print(f"Error loading template '{name}': {e}")
            return None
    
    def find_template(self, screenshot: np.ndarray, template_name: str, 
                     confidence: float = 0.8) -> Optional[Dict]:
        """
        Find a template in the screenshot using template matching.
        
        Args:
            screenshot: Screenshot to search in (BGR format)
            template_name: Name of the template to find
            confidence: Minimum confidence threshold (0.0 to 1.0)
            
        Returns:
            Dictionary with match info if found:
            - confidence: Match confidence value
            - center: (x, y) center coordinates of the match
            - top_left: (x, y) top-left coordinates
            - bottom_right: (x, y) bottom-right coordinates
            Returns None if not found or confidence too low
        """
        # Normalize template name - remove .png if present
        clean_template_name = template_name[:-4] if template_name.endswith('.png') else template_name
        
        template = self.load_template(clean_template_name)
        
        if template is None:
            # Check if template file exists
            template_path = os.path.join(self.templates_dir, f"{clean_template_name}.png")
            if not os.path.exists(template_path):
                # Only log this once per template to avoid spam
                if not hasattr(self, '_missing_templates_logged'):
                    self._missing_templates_logged = set()
                
                if clean_template_name not in self._missing_templates_logged:
                    print(f"Template file not found: {template_path}")
                    self._missing_templates_logged.add(clean_template_name)
            
            return None
        
        try:
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Debug info - log the actual confidence found vs required
            if not hasattr(self, '_debug_confidence_logged'):
                self._debug_confidence_logged = {}
            
            template_key = f"{template_name}_{confidence}"
            if template_key not in self._debug_confidence_logged:
                print(f"Template '{template_name}': Best match confidence {max_val:.3f}, Required: {confidence:.3f}")
                self._debug_confidence_logged[template_key] = True
            
            # Check if confidence meets threshold
            if max_val < confidence:
                return None
            
            # Calculate match coordinates
            template_height, template_width = template.shape[:2]
            top_left = max_loc
            bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
            center = (top_left[0] + template_width // 2, top_left[1] + template_height // 2)
            
            return {
                'confidence': max_val,
                'center': center,
                'top_left': top_left,
                'bottom_right': bottom_right,
                'template_name': clean_template_name
            }
            
        except Exception as e:
            print(f"Error finding template '{template_name}': {e}")
            return None
    
    def find_multiple_templates(self, screenshot: np.ndarray, 
                              template_rules: List[Dict]) -> List[Dict]:
        """
        Find multiple templates in a screenshot.
        
        Args:
            screenshot: Screenshot to search in (BGR format)
            template_rules: List of rule dictionaries containing:
                - name: Template name
                - confidence: Minimum confidence threshold
                - action: Action to perform if found
                
        Returns:
            List of match dictionaries for all found templates
        """
        matches = []
        
        for rule in template_rules:
            template_name = rule.get('name')
            confidence = rule.get('confidence', 0.8)
            
            if not template_name:
                continue
            
            match = self.find_template(screenshot, template_name, confidence)
            
            if match:
                # Add rule info to match
                match['rule'] = rule
                matches.append(match)
        
        return matches
    
    def get_template_list(self) -> List[str]:
        """
        Get a list of all available template names.
        
        Returns:
            List of template names (without file extensions)
        """
        templates = []
        
        try:
            if os.path.exists(self.templates_dir):
                for filename in os.listdir(self.templates_dir):
                    if filename.endswith('.png'):
                        template_name = filename[:-4]  # Remove .png extension
                        templates.append(template_name)
        except Exception as e:
            print(f"Error listing templates: {e}")
        
        return templates
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template file.
        
        Args:
            name: Name of the template to delete (with or without .png extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Normalize name - remove .png if present
            clean_name = name[:-4] if name.endswith('.png') else name
            
            template_path = os.path.join(self.templates_dir, f"{clean_name}.png")
            
            if os.path.exists(template_path):
                os.remove(template_path)
                
                # Remove from cache
                if clean_name in self.templates_cache:
                    del self.templates_cache[clean_name]
                
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting template '{name}': {e}")
            return False
    
    def clear_template_cache(self):
        """Clear the template cache to force reloading from disk."""
        self.templates_cache.clear()
    
    def visualize_match(self, screenshot: np.ndarray, match: Dict) -> np.ndarray:
        """
        Draw a rectangle around a match for visualization.
        
        Args:
            screenshot: Original screenshot
            match: Match dictionary from find_template
            
        Returns:
            Screenshot with rectangle drawn around the match
        """
        try:
            # Create a copy to avoid modifying the original
            viz_image = screenshot.copy()
            
            top_left = match['top_left']
            bottom_right = match['bottom_right']
            confidence = match['confidence']
            
            # Draw rectangle
            cv2.rectangle(viz_image, top_left, bottom_right, (0, 255, 0), 2)
            
            # Add confidence text
            text = f"{match['template_name']}: {confidence:.2f}"
            cv2.putText(viz_image, text, (top_left[0], top_left[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            return viz_image
            
        except Exception as e:
            print(f"Error visualizing match: {e}")
            return screenshot


class TemplateManager:
    """Manages template files and provides UI integration support."""
    
    def __init__(self, image_detector: ImageDetector):
        self.image_detector = image_detector
        self.templates_dir = image_detector.templates_dir
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template files."""
        templates = []
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith('.png'):
                    templates.append(file)
        return sorted(templates)
    
    def template_exists(self, template_name: str) -> bool:
        """Check if a template file exists."""
        if not template_name.endswith('.png'):
            template_name += '.png'
        template_path = os.path.join(self.templates_dir, template_name)
        return os.path.exists(template_path)
    
    def get_template_info(self, template_name: str) -> Dict:
        """Get detailed information about a template."""
        if not template_name.endswith('.png'):
            template_name += '.png'
        template_path = os.path.join(self.templates_dir, template_name)
        
        info = {
            'name': template_name,
            'path': template_path,
            'exists': os.path.exists(template_path),
            'size': None,
            'dimensions': None,
            'file_size': None,
            'modified': None
        }
        
        if info['exists']:
            try:
                # Get file info
                stat = os.stat(template_path)
                info['file_size'] = stat.st_size
                info['modified'] = stat.st_mtime
                
                # Get image dimensions
                with Image.open(template_path) as img:
                    info['dimensions'] = img.size
                    info['size'] = f"{img.size[0]}x{img.size[1]}"
            except Exception as e:
                print(f"Error getting template info: {e}")
        
        return info
    
    def create_thumbnail(self, template_name: str, max_size: int = 100) -> Optional[Image.Image]:
        """Create a thumbnail of the template image."""
        try:
            if not template_name.endswith('.png'):
                template_name += '.png'
            template_path = os.path.join(self.templates_dir, template_name)
            
            if not os.path.exists(template_path):
                return None
            
            with Image.open(template_path) as img:
                # Create thumbnail maintaining aspect ratio
                img_copy = img.copy()
                img_copy.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                return img_copy
                
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None
    
    def validate_template_file(self, template_path: str) -> Tuple[bool, str]:
        """
        Validate a template file.
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        try:
            if not os.path.exists(template_path):
                return False, "Template file does not exist"
            
            # Check file size
            file_size = os.path.getsize(template_path)
            if file_size == 0:
                return False, "Template file is empty"
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                return False, "Template file is too large (max 10MB)"
            
            # Check if it's a valid image
            try:
                with Image.open(template_path) as img:
                    # Check dimensions
                    width, height = img.size
                    if width < 5 or height < 5:
                        return False, "Template is too small (minimum 5x5 pixels)"
                    
                    if width > 2000 or height > 2000:
                        return False, "Template is too large (maximum 2000x2000 pixels)"
                    
                    # Check format
                    if img.format not in ['PNG']:
                        return False, "Template must be in PNG format"
                    
                    return True, ""
                    
            except Exception as e:
                return False, f"Invalid image file: {e}"
                
        except Exception as e:
            return False, f"Error validating template: {e}"
    
    def test_template_detection(self, template_name: str, screenshot: np.ndarray, confidence_levels: List[float] = None) -> Dict:
        """
        Test template detection at various confidence levels.
        
        Returns:
            Dictionary with test results
        """
        if confidence_levels is None:
            confidence_levels = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        if not template_name.endswith('.png'):
            template_name = template_name[:-4]  # Remove .png for detector
        
        results = {
            'template': template_name,
            'found_at_levels': [],
            'best_confidence': 0.0,
            'recommended_confidence': 0.5
        }
        
        try:
            for confidence in confidence_levels:
                match = self.image_detector.find_template(screenshot, template_name, confidence)
                if match:
                    results['found_at_levels'].append({
                        'threshold': confidence,
                        'actual_confidence': match['confidence']
                    })
                    results['best_confidence'] = max(results['best_confidence'], match['confidence'])
            
            # Calculate recommended confidence
            if results['found_at_levels']:
                results['recommended_confidence'] = max(0.5, results['best_confidence'] - 0.1)
            
        except Exception as e:
            results['error'] = str(e)
        
        return results