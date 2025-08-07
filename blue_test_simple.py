#!/usr/bin/env python3
"""
Simple blue detection test without OpenCV windows
"""

import cv2
import numpy as np
import pyautogui

def test_blue_simple():
    print("🔵 Simple Blue Detection Test")
    print("=" * 30)
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    print(f"📏 Screen size: {screen.shape}")
    
    # Convert to HSV
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # Blue range
    lower_blue = np.array([100, 150, 150])
    upper_blue = np.array([130, 255, 255])
    
    # Create mask
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Find contours
    contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"🔍 Found {len(contours)} total contours")
    
    # Filter contours
    valid_contours = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)
        
        print(f"   Contour {i}: area={area:.0f}, size={w}x{h}")
        
        if area > 500 and area < 10000:
            aspect_ratio = w / h
            if 0.5 < aspect_ratio < 2.0:
                valid_contours.append(contour)
                center_x = x + w // 2
                center_y = y + h // 2
                print(f"   ✅ Valid contour at ({center_x}, {center_y})")
    
    print(f"🎯 Found {len(valid_contours)} valid contours")
    
    if valid_contours:
        print("✅ Blue outlines detected! Ready to click.")
        for i, contour in enumerate(valid_contours):
            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            print(f"   🦀 Crab candidate {i+1}: ({center_x}, {center_y})")
    else:
        print("❌ No valid blue contours found")

if __name__ == "__main__":
    test_blue_simple()
