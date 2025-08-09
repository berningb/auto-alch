#!/usr/bin/env python3
"""
Simple Dart Detection Test
"""

import cv2
import numpy as np
import pyautogui
import time
import os


def segment_blue_regions(screen_bgr):
    hsv = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2HSV)
    # Broad blue range suitable for darts; tune if needed
    lower = np.array([100, 120, 120])
    upper = np.array([130, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
    return mask


def find_best_blue_roi(mask, screen_shape, min_area=800, max_area=150000, edge_margin=2):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    h_img, w_img = screen_shape[:2]
    best = None
    best_area = 0.0
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
    return best


def test_dart_detection():
    """Continuously test dart icon detection on screen"""
    print("🎯 Testing Dart Detection")
    print("=" * 40)

    images_dir = os.path.join(os.path.dirname(__file__), "images")
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

    # Load dart templates dynamically (any dart*.png)
    templates = {}
    current_dir = os.path.dirname(__file__)
    for dir_path in [images_dir, current_dir]:
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            lower = fname.lower()
            if not lower.startswith("dart") or not lower.endswith(".png"):
                continue
            full_path = os.path.join(dir_path, fname)
            if not os.path.exists(full_path):
                continue
            img = cv2.imread(full_path)
            if img is not None:
                templates[fname] = img
                print(f"✅ Loaded {fname} from {full_path}")

    if not templates:
        print("❌ No dart templates found!")
        return

    print(f"\n📁 Loaded {len(templates)} template(s)")
    
    while True:
        try:
            # Capture screen
            screenshot = pyautogui.screenshot()
            screen = np.array(screenshot)
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            print("\n🔍 Scanning for darts (color-first)...")

            mask = segment_blue_regions(screen)
            roi = find_best_blue_roi(mask, screen.shape)
            if roi is None:
                print("   🔭 No valid blue region found")
            else:
                x, y, w, h = roi
                cx, cy = x + w // 2, y + h // 2
                print(f"   🎨 Blue ROI at ({cx}, {cy}) size {w}x{h}")
                pad = 8
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(screen.shape[1], x + w + pad), min(screen.shape[0], y + h + pad)
                roi_img = screen[y1:y2, x1:x2]

                best_name = None
                best_conf = 0.0
                best_pos = (cx, cy)
                roi_gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
                for name, tmpl in templates.items():
                    try:
                        tmpl_gray = cv2.cvtColor(tmpl, cv2.COLOR_BGR2GRAY)
                        res = cv2.matchTemplate(roi_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(res)
                        if max_val > best_conf:
                            th, tw = tmpl_gray.shape
                            best_conf = float(max_val)
                            best_pos = (x1 + max_loc[0] + tw // 2, y1 + max_loc[1] + th // 2)
                            best_name = name
                    except Exception:
                        pass

                if best_name:
                    print(f"   🎯 ROI template '{best_name}' matched at {best_pos} (conf {best_conf:.3f})")
                else:
                    print("   ⚪ No template confirmation; using color-only center")

                # Hover over the predicted position briefly for visual confirmation
                try:
                    sx = int(round(best_pos[0] / max(1e-6, scale_x)))
                    sy = int(round(best_pos[1] / max(1e-6, scale_y)))
                    pyautogui.moveTo(sx, sy, duration=0.15)
                except Exception:
                    pass
                
            
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
