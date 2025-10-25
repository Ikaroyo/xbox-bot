"""
Create a simple test template for bot testing.
This creates a basic image that can be used to test template detection.
"""

import cv2
import numpy as np
import os

def create_test_template():
    """Create a simple test template image."""
    
    # Create a 100x50 image with white background
    template = np.ones((50, 100, 3), dtype=np.uint8) * 255
    
    # Add some colored rectangles to make it distinctive
    cv2.rectangle(template, (10, 10), (40, 40), (0, 255, 0), -1)  # Green rectangle
    cv2.rectangle(template, (60, 10), (90, 40), (255, 0, 0), -1)  # Blue rectangle
    
    # Add text
    cv2.putText(template, "TEST", (25, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # Create templates directory if it doesn't exist
    templates_dir = "templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # Save the template
    template_path = os.path.join(templates_dir, "test_template.png")
    cv2.imwrite(template_path, template)
    
    print(f"Test template created: {template_path}")
    print("This template contains:")
    print("- Green rectangle on the left")
    print("- Blue rectangle on the right") 
    print("- Black 'TEST' text in the center")
    print("- Size: 100x50 pixels")
    print("\nTo use this template:")
    print("1. Create a rule named 'TestRule'")
    print("2. Set template to 'test_template.png'")
    print("3. Set confidence to 0.8")
    print("4. Set action to 'A'")
    print("5. Display this image on your screen and start the bot")

if __name__ == "__main__":
    create_test_template()