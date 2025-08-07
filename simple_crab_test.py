#!/usr/bin/env python3
"""
Simple crab detection test
"""

import cv2
import numpy as np
import pyautogui
import time

def test_crab():
    print("🦀 Simple Crab Detection Test")
    print("=" * 30)
    
    # Load crab template
    crab_template = cv2.imread("crab_template.png")
    if crab_template is None:
        print("❌ Crab template not found!")
        return
    
    print(f"📏 Crab template size: {crab_template.shape}")
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    print(f"📏 Screen size: {screen.shape}")
    
    # Convert to grayscale
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(crab_template, cv2.COLOR_BGR2GRAY)
    
    # Template matching
    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"🎯 Best match: {max_loc}")
    print(f"🎯 Confidence: {max_val:.3f}")
    
    # Calculate center
    h, w = template_gray.shape
    center_x = max_loc[0] + w // 2
    center_y = max_loc[1] + h // 2
    
    print(f"📍 Calculated center: ({center_x}, {center_y})")
    
    # Check bounds
    screen_height, screen_width = screen.shape[:2]
    print(f"📐 Screen bounds: {screen_width}x{screen_height}")
    
    if center_x < 0 or center_x > screen_width or center_y < 0 or center_y > screen_height:
        print("❌ Position outside screen bounds!")
    else:
        print("✅ Position within screen bounds")
        
        # Test if we would click there
        print(f"🖱️ Would click at: ({center_x}, {center_y})")
        
        # Show the area that would be clicked
        cv2.imshow("Crab Template", crab_template)
        
        # Draw rectangle on screen
        detected_screen = screen.copy()
        cv2.rectangle(detected_screen, max_loc, (max_loc[0] + w, max_loc[1] + h), (0, 255, 0), 2)
        cv2.circle(detected_screen, (center_x, center_y), 5, (0, 0, 255), -1)
        cv2.imshow("Detected Area", detected_screen)
        
        print("Press any key to close...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_crab()
