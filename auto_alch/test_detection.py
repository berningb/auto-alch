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
    """Test dart detection (color-first with ROI template confirmation)"""
    print("\n🎯 Testing Darts")
    print("-" * 40)
    
    # Load dart templates dynamically (any dart*.png)
    templates = {}
    current_dir = os.path.dirname(__file__)
    for dir_path in [os.path.join(os.path.dirname(__file__), "images"), current_dir]:
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            if fname.lower().startswith("dart") and fname.lower().endswith(".png"):
                full = os.path.join(dir_path, fname)
                if os.path.exists(full):
                    img = cv2.imread(full)
                    if img is not None:
                        templates[fname] = img
                        print(f"✅ Loaded {fname}")
    
    if not templates:
        print("❌ No dart templates found!")
        return None
    
    # Capture screen
    screenshot = pyautogui.screenshot()
    screen = np.array(screenshot)
    screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)

    # Color-first search for blue region
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    lower = np.array([100, 120, 120])
    upper = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No blue regions found")
        return None

    h_img, w_img = screen.shape[:2]
    min_area, max_area, edge_margin = 800.0, 150000.0, 2
    best = None
    best_area = 0
    for c in contours:
        area = float(cv2.contourArea(c))
        if area < min_area or area > max_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if x <= edge_margin or y <= edge_margin or (x + w) >= (w_img - edge_margin) or (y + h) >= (h_img - edge_margin):
            continue
        if area > best_area:
            best_area = area
            best = (x, y, w, h)

    if best is None:
        print("No valid ROI from blue regions")
        return None

    x, y, w, h = best
    pad = 8
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2, y2 = min(w_img, x + w + pad), min(h_img, y + h + pad)
    roi = screen[y1:y2, x1:x2]

    # Confirm within ROI using available templates
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    best_conf, best_loc, best_name = 0.0, None, None
    for name, tmpl in templates.items():
        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(roi_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best_conf:
            th, tw = tmpl_gray.shape
            best_conf = float(max_val)
            best_loc = (x1 + max_loc[0] + tw // 2, y1 + max_loc[1] + th // 2)
            best_name = name

    if best_loc:
        print(f"Confirmed by template '{best_name}' at {best_loc} (conf {best_conf:.3f})")
        try:
            pyautogui.moveTo(best_loc[0], best_loc[1], duration=0.15)
        except Exception:
            pass
        return best_loc
    else:
        center = (x + w // 2, y + h // 2)
        print(f"Using color-only center {center}")
        try:
            pyautogui.moveTo(center[0], center[1], duration=0.15)
        except Exception:
            pass
        return center

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
    
    # Determine scaling (image pixels vs OS coordinates)
    try:
        sw, sh = pyautogui.size()
        shot = pyautogui.screenshot()
        arr = np.array(shot)
        ih, iw = arr.shape[:2]
        scale_x = max(1e-6, iw / float(sw))
        scale_y = max(1e-6, ih / float(sh))
    except Exception:
        scale_x = scale_y = 1.0
    
    try:
        while True:
            alch_loc = test_alch_detection()
            dart_loc = test_dart_detection()
            # If we got a location, hover using scaled coordinates for verification
            if dart_loc:
                try:
                    sx = int(round(dart_loc[0] / max(1e-6, scale_x)))
                    sy = int(round(dart_loc[1] / max(1e-6, scale_y)))
                    pyautogui.moveTo(sx, sy, duration=0.15)
                except Exception:
                    pass
            
            print("\n" + "=" * 40)
            time.sleep(2)  # Wait 2 seconds before next scan
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")

if __name__ == "__main__":
    main()
