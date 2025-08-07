#!/usr/bin/env python3
"""
Test script for blue outline detection
"""

import cv2
import numpy as np
import pyautogui
import time

def test_blue_detection():
    """Test blue outline detection with different parameters"""
    print("🔵 Testing Blue Outline Detection")
    print("=" * 40)
    
    # Capture current screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    print(f"📏 Screen size: {screen.shape}")
    
    # Convert to HSV
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # Test different blue ranges
    blue_ranges = [
        ("Dark Blue", np.array([100, 150, 150]), np.array([130, 255, 255])),
        ("Bright Blue", np.array([110, 100, 100]), np.array([130, 255, 255])),
        ("Light Blue", np.array([100, 50, 50]), np.array([130, 255, 255])),
        ("Narrow Blue", np.array([115, 150, 150]), np.array([125, 255, 255])),
    ]
    
    for name, lower, upper in blue_ranges:
        print(f"\n🔍 Testing {name} range...")
        
        # Create mask
        blue_mask = cv2.inRange(hsv, lower, upper)
        
        # Find contours
        contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours
        valid_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            
            if area > 500 and area < 10000:
                aspect_ratio = w / h
                if 0.5 < aspect_ratio < 2.0:
                    valid_contours.append(contour)
        
        print(f"   Found {len(valid_contours)} valid contours")
        
        if valid_contours:
            # Show the mask and detected areas
            cv2.imshow(f"Blue Mask - {name}", blue_mask)
            
            # Draw contours on screen
            result_screen = screen.copy()
            cv2.drawContours(result_screen, valid_contours, -1, (0, 255, 0), 2)
            
            # Draw centers
            for contour in valid_contours:
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(result_screen, (center_x, center_y), 5, (0, 0, 255), -1)
                print(f"   📍 Contour center: ({center_x}, {center_y})")
            
            cv2.imshow(f"Detected Areas - {name}", result_screen)
    
    print("\nPress any key to close windows...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_blue_detection()
