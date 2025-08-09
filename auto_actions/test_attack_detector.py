#!/usr/bin/env python3
"""
Test script for the attack detector
Quickly test damage number detection without the full monitoring loop
"""

import os
import sys
import cv2
import numpy as np

# Add auto_actions to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

from attack_detector import detect_orange_damage_numbers
from funcs import AutoActionFunctions

def test_current_screen():
    """Test damage detection on current screen"""
    print("🧪 Testing attack detector on current screen...")
    
    # Capture current screen
    funcs = AutoActionFunctions()
    frame = funcs.capture_screen()
    
    if frame is None:
        print("❌ Failed to capture screen")
        return
    
    print(f"📸 Screen captured: {frame.shape}")
    
    # Detect damage numbers
    detected_numbers = detect_orange_damage_numbers(frame)
    
    if detected_numbers:
        print(f"✅ Found {len(detected_numbers)} damage number(s):")
        for damage_value, position, confidence in detected_numbers:
            print(f"  💥 Damage: {damage_value} at {position} (confidence: {confidence:.2f})")
    else:
        print("ℹ️ No damage numbers detected on current screen")
        print("💡 Try capturing a screen with visible orange damage numbers")

if __name__ == "__main__":
    test_current_screen()

