#!/usr/bin/env python3
"""
Demo Attack Detector - Shows basic functionality without requiring OCR

This demonstrates the orange color detection part of the attack detector.
For full functionality with number recognition, install pytesseract.
"""

import os
import sys
import cv2
import numpy as np
import time

# Add auto_actions to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from funcs import AutoActionFunctions

# HSV ranges for RuneScape orange damage numbers (same as main detector)
HSV_ORANGE_DAMAGE_RANGES = [
    (np.array([20, 200, 200]), np.array([35, 255, 255])),
    (np.array([15, 150, 150]), np.array([40, 255, 255])),
    (np.array([10, 100, 100]), np.array([45, 255, 255])),
]

def demo_orange_detection():
    """Demonstrate orange damage number detection"""
    print("🎯 Attack Detector Demo")
    print("=" * 40)
    print("This demo shows orange color detection for damage numbers.")
    print("Without OCR, we can detect orange number-like shapes but not read them.")
    print("To get actual damage values, install pytesseract OCR.")
    print("=" * 40)
    
    funcs = AutoActionFunctions()
    
    print("\n📸 Capturing current screen...")
    frame = funcs.capture_screen()
    
    if frame is None:
        print("❌ Failed to capture screen")
        return
    
    print(f"✅ Screen captured: {frame.shape[1]}x{frame.shape[0]} pixels")
    
    # Convert to HSV for orange detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Create mask for orange damage colors
    orange_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    
    for i, (lower, upper) in enumerate(HSV_ORANGE_DAMAGE_RANGES):
        mask_range = cv2.inRange(hsv, lower, upper)
        orange_mask = cv2.bitwise_or(orange_mask, mask_range)
        range_pixels = cv2.countNonZero(mask_range)
        print(f"🟠 Orange range {i+1}: {range_pixels} pixels")
    
    # Count total orange pixels
    total_orange_pixels = cv2.countNonZero(orange_mask)
    print(f"🎨 Total orange pixels found: {total_orange_pixels}")
    
    if total_orange_pixels < 10:
        print("\nℹ️ Very few orange pixels detected.")
        print("💡 This is normal if there are no damage numbers currently visible.")
        return
    
    # Find contours for potential damage numbers
    contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"🔍 Found {len(contours)} orange contours")
    
    # Filter for number-like shapes
    potential_numbers = []
    
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        
        # Filter by size - damage numbers are typically small to medium sized
        if 20 < area < 5000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = h / w if w > 0 else 0
            
            # Filter by aspect ratio - numbers are typically taller than they are wide
            if 0.3 < aspect_ratio < 5.0:
                potential_numbers.append({
                    'contour_id': i,
                    'area': area,
                    'position': (x + w//2, y + h//2),
                    'size': (w, h),
                    'aspect_ratio': aspect_ratio
                })
    
    print(f"\n🎯 Found {len(potential_numbers)} potential damage number shapes:")
    
    if potential_numbers:
        for j, num in enumerate(potential_numbers[:10]):  # Show first 10
            print(f"  #{j+1}: Area={num['area']:.1f}, Position={num['position']}, "
                  f"Size={num['size']}, Aspect={num['aspect_ratio']:.2f}")
        
        if len(potential_numbers) > 10:
            print(f"  ... and {len(potential_numbers) - 10} more")
        
        print(f"\n✅ Orange number-like shapes detected successfully!")
        print(f"💡 To see actual damage values, install pytesseract:")
        print(f"   pip install pytesseract")
        print(f"   Also install Tesseract binary from: https://github.com/UB-Mannheim/tesseract/wiki")
    else:
        print("\nℹ️ No number-like orange shapes found.")
        print("💡 Try running this when damage numbers are visible on screen.")

if __name__ == "__main__":
    demo_orange_detection()

