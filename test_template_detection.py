#!/usr/bin/env python3
"""
Template Detection Tester

This utility helps debug template detection issues by:
1. Testing different confidence thresholds
2. Showing the best match confidence found
3. Saving visualizations of matches
4. Comparing template and screenshot properties
"""

import cv2
import numpy as np
import os
import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from modules.image_detector import ImageDetector
from modules.window_manager import WindowManager

def test_template_detection():
    """Test template detection with current screenshot."""
    
    print("Template Detection Tester")
    print("=" * 40)
    
    # Initialize components
    window_manager = WindowManager()
    image_detector = ImageDetector()
    
    # Find Xbox window
    print("1. Looking for Xbox window...")
    windows = window_manager.find_windows_by_title("Xbox")
    
    if not windows:
        print("❌ No Xbox window found")
        return
    
    window = windows[0]
    print(f"✅ Found window: {window['process_name']} (PID: {window['pid']})")
    
    # Capture screenshot
    print("\n2. Capturing screenshot...")
    capture_area = window_manager.capture_window_area(window)
    if not capture_area:
        print("❌ Could not get window capture area")
        return
    
    screenshot = image_detector.capture_screenshot(capture_area)
    if screenshot is None:
        print("❌ Could not capture screenshot")
        return
    
    print(f"✅ Screenshot captured: {screenshot.shape} (height, width, channels)")
    
    # Get available templates
    print("\n3. Available templates:")
    
    # First, check what files actually exist
    templates_dir = "templates"
    actual_files = []
    if os.path.exists(templates_dir):
        for file in os.listdir(templates_dir):
            if file.endswith('.png'):
                name_without_ext = file[:-4]  # Remove .png
                actual_files.append(name_without_ext)
    
    print(f"   PNG files in {templates_dir}/:")
    for i, file in enumerate(actual_files):
        print(f"     {i+1}. {file}.png")
    
    # Then check what ImageDetector can load
    templates = image_detector.get_template_list()
    print(f"   Templates loadable by ImageDetector:")
    for i, template in enumerate(templates):
        print(f"     {i+1}. {template}")
    
    if not templates and not actual_files:
        print("❌ No templates found in templates/ directory")
        return
    
    # Use actual files if ImageDetector list is empty
    template_list = templates if templates else actual_files
    
    # Let user choose template
    try:
        choice = input(f"\nChoose template (1-{len(template_list)}): ")
        template_index = int(choice) - 1
        
        if template_index < 0 or template_index >= len(template_list):
            print("❌ Invalid choice")
            return
        
        template_name = template_list[template_index]
        
    except (ValueError, KeyboardInterrupt):
        print("❌ Invalid input or cancelled")
        return
    
    print(f"\n4. Testing template: {template_name}")
    
    # Load template
    template = image_detector.load_template(template_name)
    if template is None:
        print(f"❌ Could not load template: {template_name}")
        return
    
    print(f"✅ Template loaded: {template.shape} (height, width, channels)")
    
    # Test different confidence levels
    print(f"\n5. Testing different confidence levels...")
    confidence_levels = [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
    
    # Get best match first
    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"\n📊 Template Matching Results:")
    print(f"   Best match confidence: {max_val:.4f}")
    print(f"   Best match location: {max_loc}")
    
    found_any = False
    for confidence in confidence_levels:
        match = image_detector.find_template(screenshot, template_name, confidence)
        
        if match:
            print(f"   ✅ Confidence {confidence:.2f}: FOUND (actual: {match['confidence']:.4f})")
            found_any = True
        else:
            print(f"   ❌ Confidence {confidence:.2f}: not found")
    
    if not found_any:
        print(f"\n⚠️  Template not found at any tested confidence level!")
        print(f"    Best match was {max_val:.4f}")
        print(f"    Try lowering confidence to {max_val - 0.01:.2f} or lower")
    
    # Save visualization
    print(f"\n6. Saving visualization...")
    
    debug_dir = "debug_template_test"
    if not os.path.exists(debug_dir):
        os.makedirs(debug_dir)
    
    # Save original screenshot
    screenshot_path = os.path.join(debug_dir, f"screenshot_{template_name}.png")
    cv2.imwrite(screenshot_path, screenshot)
    
    # Save template
    template_path = os.path.join(debug_dir, f"template_{template_name}.png")
    cv2.imwrite(template_path, template)
    
    # Create visualization with best match marked
    vis_screenshot = screenshot.copy()
    template_height, template_width = template.shape[:2]
    
    # Draw rectangle at best match location
    top_left = max_loc
    bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
    
    # Different colors based on confidence
    if max_val >= 0.8:
        color = (0, 255, 0)  # Green - good match
    elif max_val >= 0.6:
        color = (0, 255, 255)  # Yellow - medium match
    else:
        color = (0, 0, 255)  # Red - poor match
    
    cv2.rectangle(vis_screenshot, top_left, bottom_right, color, 2)
    
    # Add confidence text
    cv2.putText(vis_screenshot, f"Best: {max_val:.3f}", 
               (top_left[0], top_left[1] - 10), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    
    vis_path = os.path.join(debug_dir, f"visualization_{template_name}.png")
    cv2.imwrite(vis_path, vis_screenshot)
    
    print(f"✅ Files saved to {debug_dir}/:")
    print(f"   - {screenshot_path}")
    print(f"   - {template_path}")
    print(f"   - {vis_path}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if max_val >= 0.8:
        print(f"   ✅ Template should work well with confidence 0.8")
    elif max_val >= 0.6:
        print(f"   ⚠️  Lower confidence to 0.6-0.7 for detection")
        print(f"   🔍 Check if template matches exactly what's on screen")
    else:
        print(f"   ❌ Template may not match current screen content")
        print(f"   📷 Consider recapturing the template")
        print(f"   🎯 Make sure template shows distinctive features")
        print(f"   📐 Check if window resolution/scaling changed")
    
    print(f"\n🎮 To fix in Stumble Bot:")
    if max_val < 0.8:
        suggested_confidence = max(0.5, max_val - 0.05)
        print(f"   1. Set confidence to {suggested_confidence:.2f} or lower")
        print(f"   2. Or recapture template when image is on screen")
    
    print(f"   3. Use Debug Mode in app for real-time screenshots")

if __name__ == "__main__":
    try:
        test_template_detection()
    except KeyboardInterrupt:
        print("\n\nTesting cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()