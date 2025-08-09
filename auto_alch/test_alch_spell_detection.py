#!/usr/bin/env python3
"""
Test Alch Spell Detection - Testing both templates
"""

import cv2
import numpy as np
import pyautogui
import time
import os

def press_key(key):
    """Press a key with human-like timing"""
    print(f"\n⌨️  Pressing '{key}' to open spellbook...")
    time.sleep(0.2)
    pyautogui.press(key)
    time.sleep(1.0)  # Wait longer for spellbook to open

def find_alch_spell(screen, template, template_name):
    """Find alch spell with a specific template"""
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"\nTesting {template_name}:")
    print(f"Match confidence: {max_val:.3f}")
    
    if max_val >= 0.5:  # Using lower threshold for reporting
        h, w = template_gray.shape
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        return (center_x, center_y), max_val
    
    return None, max_val

def test_alch_detection():
    """Test alch spell detection with both templates"""
    print("\n🔮 Testing Alch Spell")
    print("-" * 40)
    
    # Load alch spell templates
    templates = {}
    
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    alch_path_candidates = [
        os.path.join(images_dir, "alc-spell.png"),
        os.path.join(os.path.dirname(__file__), "alc-spell.png"),
    ]
    alch_path = next((p for p in alch_path_candidates if os.path.exists(p)), alch_path_candidates[0])
    if os.path.exists(alch_path):
        templates["alc-spell.png"] = cv2.imread(alch_path)
        print("✅ Loaded alc-spell.png")
    
    alch2_path_candidates = [
        os.path.join(images_dir, "alc-spell2.png"),
        os.path.join(os.path.dirname(__file__), "alc-spell2.png"),
    ]
    alch2_path = next((p for p in alch2_path_candidates if os.path.exists(p)), alch2_path_candidates[0])
    if os.path.exists(alch2_path):
        templates["alc-spell2.png"] = cv2.imread(alch2_path)
        print("✅ Loaded alc-spell2.png")
    
    # New: third template
    alch3_path_candidates = [
        os.path.join(images_dir, "alc-spell3.png"),
        os.path.join(os.path.dirname(__file__), "alc-spell3.png"),
    ]
    alch3_path = next((p for p in alch3_path_candidates if os.path.exists(p)), alch3_path_candidates[0])
    if os.path.exists(alch3_path):
        templates["alc-spell3.png"] = cv2.imread(alch3_path)
        print("✅ Loaded alc-spell3.png")
    
    if not templates:
        print("❌ No alch spell templates found!")
        return None
    
    # First try without pressing '3'
    print("\n1️⃣ Checking if spell is already visible:")
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    # Try both templates
    best_confidence = 0
    best_location = None
    best_template = None
    
    for template_name, template in templates.items():
        location, confidence = find_alch_spell(screen, template, template_name)
        if confidence > best_confidence:
            best_confidence = confidence
            best_location = location
            best_template = template_name
    
    print(f"\nBest initial result: {best_template if best_template else 'None'}")
    print(f"Best confidence: {best_confidence:.3f}")
    
    # If confidence is too low, press '3' and check again
    if best_confidence < 0.7:  # Using a higher threshold to be more strict
        print("❌ Spell not found - spellbook might be closed")
        press_key('3')
        
        # Check again after pressing '3'
        print("\n2️⃣ Checking after pressing '3':")
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
        
        # Try both templates again
        best_confidence = 0
        best_location = None
        best_template = None
        
        for template_name, template in templates.items():
            location, confidence = find_alch_spell(screen, template, template_name)
            if confidence > best_confidence:
                best_confidence = confidence
                best_location = location
                best_template = template_name
        
        print(f"\nBest result after '3': {best_template if best_template else 'None'}")
        print(f"Best confidence: {best_confidence:.3f}")
    
    # Report final results
    if best_confidence >= 0.7:
        print(f"\n✅ Found spell using {best_template}")
        print(f"Location: {best_location}")
        print(f"Confidence: {best_confidence:.3f}")
        return best_location
    else:
        print(f"\n❌ Couldn't find spell with either template")
        print(f"Best confidence was only {best_confidence:.3f}")
        return None

def main():
    """Main function"""
    print("🔍 Alch Spell Detection Test")
    print("=" * 40)
    print("Testing High Alchemy spell detection")
    print("Using alc-spell.png, alc-spell2.png, and alc-spell3.png if present")
    print("Will press '3' if spell is not found")
    print("\nPress Ctrl+C to stop")
    print("=" * 40)
    
    try:
        while True:
            test_alch_detection()
            print("\n" + "=" * 40)
            time.sleep(2)  # Wait 2 seconds before next scan
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")

if __name__ == "__main__":
    main()