#!/usr/bin/env python3
"""
Test Detection Script - Tests both Alch Spell and Dart detection
"""

import cv2
import numpy as np
import pyautogui
import time
import os

def test_alch_detection():
    """Test alch spell detection"""
    print("\n🔮 Testing Alch Spell")
    print("-" * 40)
    
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    alch_path_candidates = [
        os.path.join(images_dir, "alc-spell.png"),
        os.path.join(os.path.dirname(__file__), "alc-spell.png"),
    ]
    alch_path = next((p for p in alch_path_candidates if os.path.exists(p)), alch_path_candidates[0])
    if not os.path.exists(alch_path):
        print("❌ Alch spell template not found!")
        return None
        
    template = cv2.imread(alch_path)
    if template is None:
        print("❌ Failed to load alch spell template!")
        return None
        
    print("✅ Loaded alch spell template")
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    # Convert to grayscale
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # Template matching
    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"Best match confidence: {max_val:.3f}")
    
    # Test different thresholds
    thresholds = [0.5, 0.6, 0.7, 0.8]
    location = None
    
    for threshold in thresholds:
        if max_val >= threshold:
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            location = (center_x, center_y)
            print(f"✅ Threshold {threshold}: Found at ({center_x}, {center_y})")
        else:
            print(f"❌ Threshold {threshold}: Not found")
            
    return location

def test_dart_detection():
    """Test dart detection"""
    print("\n🎯 Testing Darts")
    print("-" * 40)
    
    # Try dart templates (look in images/ first)
    templates = {}
    dart_path_candidates = [
        os.path.join(images_dir, "dart.png"),
        os.path.join(os.path.dirname(__file__), "dart.png"),
    ]
    dart_path = next((p for p in dart_path_candidates if os.path.exists(p)), dart_path_candidates[0])
    if os.path.exists(dart_path):
        templates["dart.png"] = cv2.imread(dart_path)
        print("✅ Loaded dart.png")
    
    dart2_path_candidates = [
        os.path.join(images_dir, "dart2.png"),
        os.path.join(os.path.dirname(__file__), "dart2.png"),
    ]
    dart2_path = next((p for p in dart2_path_candidates if os.path.exists(p)), dart2_path_candidates[0])
    if os.path.exists(dart2_path):
        templates["dart2.png"] = cv2.imread(dart2_path)
        print("✅ Loaded dart2.png")
    
    if not templates:
        print("❌ No dart templates found!")
        return None
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    
    best_confidence = 0
    best_location = None
    best_template = None
    
    for template_name, template in templates.items():
        print(f"\nTesting {template_name}:")
        
        # Convert to grayscale
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        print(f"Match confidence: {max_val:.3f}")
        
        if max_val > best_confidence:
            best_confidence = max_val
            h, w = template_gray.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            best_location = (center_x, center_y)
            best_template = template_name
    
    if best_location:
        print(f"\n✨ Best result: {best_template}")
        print(f"Location: ({best_location[0]}, {best_location[1]})")
        print(f"Confidence: {best_confidence:.3f}")
    
    return best_location

def main():
    """Main function"""
    print("🔍 Detection Test Script")
    print("=" * 40)
    print("Testing both Alch Spell and Dart detection")
    print("Make sure:")
    print("1. Your spellbook is open")
    print("2. High Alchemy spell is visible")
    print("3. Darts are visible")
    print("\nPress Ctrl+C to stop")
    print("=" * 40)
    
    try:
        while True:
            alch_loc = test_alch_detection()
            dart_loc = test_dart_detection()
            
            print("\n" + "=" * 40)
            time.sleep(2)  # Wait 2 seconds before next scan
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")

if __name__ == "__main__":
    main()
