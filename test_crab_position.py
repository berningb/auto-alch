#!/usr/bin/env python3
"""
Test crab position calculation
"""

import cv2
import numpy as np
import pyautogui

def test_crab_position():
    """Test the crab position calculation"""
    print("🦀 Testing Crab Position Calculation")
    print("=" * 40)
    
    # Load templates
    crab_template = cv2.imread("crab_template.png")
    if crab_template is None:
        print("❌ Crab template not found!")
        return
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(crab_template, cv2.COLOR_BGR2GRAY)
    
    # Test different thresholds
    thresholds = [0.7, 0.6, 0.5, 0.4]
    
    for threshold in thresholds:
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        print(f"\n🔍 Testing threshold: {threshold}")
        print(f"   Best match location: {max_loc}")
        print(f"   Best confidence: {max_val:.3f}")
        
        if max_val >= threshold:
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            print(f"   Calculated center: ({center_x}, {center_y})")
            
            # Check bounds
            screen_height, screen_width = screen.shape[:2]
            if center_x < 0 or center_x > screen_width or center_y < 0 or center_y > screen_height:
                print(f"   ❌ Position outside bounds!")
            else:
                print(f"   ✅ Position within bounds")
        else:
            print(f"   ❌ Below threshold")

if __name__ == "__main__":
    test_crab_position()
