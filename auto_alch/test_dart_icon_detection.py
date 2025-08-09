#!/usr/bin/env python3
"""
Simple Dart Detection Test
"""

import cv2
import numpy as np
import pyautogui
import time
import os

def test_dart_detection():
    """Continuously test dart icon detection on screen"""
    print("🎯 Testing Dart Detection")
    print("=" * 40)

    images_dir = os.path.join(os.path.dirname(__file__), "images")

    # Load dart templates from images/ (fallback to current dir)
    templates = {}

    dart_path_candidates = [
        os.path.join(images_dir, "dart.png"),
        os.path.join(os.path.dirname(__file__), "dart.png"),
    ]
    dart_path = next((p for p in dart_path_candidates if os.path.exists(p)), dart_path_candidates[0])
    if os.path.exists(dart_path):
        templates["dart.png"] = cv2.imread(dart_path)
        print(f"✅ Loaded dart.png from {dart_path}")

    dart2_path_candidates = [
        os.path.join(images_dir, "dart2.png"),
        os.path.join(os.path.dirname(__file__), "dart2.png"),
    ]
    dart2_path = next((p for p in dart2_path_candidates if os.path.exists(p)), dart2_path_candidates[0])
    if os.path.exists(dart2_path):
        templates["dart2.png"] = cv2.imread(dart2_path)
        print(f"✅ Loaded dart2.png from {dart2_path}")

    dart3_path_candidates = [
        os.path.join(images_dir, "dart3.png"),
        os.path.join(os.path.dirname(__file__), "dart3.png"),
    ]
    dart3_path = next((p for p in dart3_path_candidates if os.path.exists(p)), dart3_path_candidates[0])
    if os.path.exists(dart3_path):
        templates["dart3.png"] = cv2.imread(dart3_path)
        print(f"✅ Loaded dart3.png from {dart3_path}")

    if not templates:
        print("❌ No dart templates found!")
        return

    print(f"\n📁 Testing {len(templates)} template(s)")
    
    while True:
        try:
            # Capture screen
            screenshot = pyautogui.screenshot()
            screen = np.array(screenshot)
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            print("\n🔍 Scanning for darts...")
            
            # Test each template
            for template_name, template in templates.items():
                print(f"\n📄 Testing {template_name}:")
                
                # Convert to grayscale
                screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                # Template matching
                result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                print(f"   Best match confidence: {max_val:.3f}")
                
                # Test different thresholds
                thresholds = [0.5, 0.6, 0.7]
                for threshold in thresholds:
                    if max_val >= threshold:
                        h, w = template_gray.shape
                        center_x = max_loc[0] + w // 2
                        center_y = max_loc[1] + h // 2
                        print(f"   ✅ Threshold {threshold}: Found at ({center_x}, {center_y})")
                    else:
                        print(f"   ❌ Threshold {threshold}: Not found")
            
            print("\n" + "="*40)
            print("Press Ctrl+C to stop")
            time.sleep(3)  # Wait 3 seconds before next scan
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("Starting Dart Detection Test...")
    print("Make sure darts are visible on screen!")
    print("Press Ctrl+C to stop")
    print()
    test_dart_detection()
