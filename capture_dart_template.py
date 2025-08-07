#!/usr/bin/env python3
"""
Capture dart template with number included
"""

import cv2
import numpy as np
import pyautogui
import time

def capture_dart_template():
    """Capture the dart template with number included"""
    print("🎯 Dart Template Capture")
    print("=" * 30)
    print("This will capture the dart template with the number above it.")
    print("The darts should be the first item in your inventory.")
    print()
    print("Instructions:")
    print("1. Make sure darts are the first item in your inventory")
    print("2. Position your mouse over the darts (including the number)")
    print("3. Press Enter when ready to capture")
    print("4. Move mouse to corner to stop")
    print()
    
    input("Press Enter when ready to capture dart template...")
    
    try:
        # Get mouse position
        x, y = pyautogui.position()
        print(f"Mouse position: ({x}, {y})")
        
        # Capture a region around the mouse (including the number above)
        # Make it larger to include the number
        region_width = 80
        region_height = 60  # Increased to include number above
        
        # Capture the region
        screenshot = pyautogui.screenshot(region=(x - region_width//2, y - region_height//2, region_width, region_height))
        
        # Convert to numpy array
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Save the template
        cv2.imwrite("dart_template.png", frame)
        
        print(f"✅ Dart template saved as 'dart_template.png'")
        print(f"📏 Template size: {frame.shape[1]}x{frame.shape[0]} pixels")
        print(f"📍 Captured at position: ({x}, {y})")
        
        # Show a preview
        cv2.imshow("Dart Template Preview", frame)
        print("Press any key to close preview...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error capturing dart template: {e}")

if __name__ == "__main__":
    capture_dart_template()
