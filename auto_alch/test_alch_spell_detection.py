#!/usr/bin/env python3
"""
Test Alch Spell Detection - Full-screen template-only multiscale over all alc-spell*.png; clicks spell when found
"""

import cv2
import numpy as np
import pyautogui
import time
import os
from datetime import datetime


def load_alch_templates():
    templates = {}
    base = os.path.dirname(__file__)
    images_dir = os.path.join(base, "images")
    for dir_path in [images_dir, base]:
        if not os.path.isdir(dir_path):
            continue
        for fname in sorted(os.listdir(dir_path)):
            lower = fname.lower()
            if not lower.startswith("alc-spell") or not lower.endswith(".png"):
                continue
            path = os.path.join(dir_path, fname)
            if not os.path.exists(path):
                continue
            img = cv2.imread(path)
            if img is None:
                continue
            templates[fname] = (img, path)
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
            print(f"✅ Loaded {fname} from {path} (modified {mtime})")
    return templates


def multiscale_match(screen_bgr, template_bgr, scales=None):
    if template_bgr is None:
        return None, 0.0
    if scales is None:
        scales = [0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15, 1.20]
    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    best_pos, best_conf = None, 0.0
    for s in scales:
        try:
            h0, w0 = template_bgr.shape[:2]
            new_w = max(2, int(round(w0 * s)))
            new_h = max(2, int(round(h0 * s)))
            if new_w < 2 or new_h < 2:
                continue
            resized = cv2.resize(template_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC)
            tmpl_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(screen_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val > best_conf:
                th, tw = tmpl_gray.shape
                best_conf = float(max_val)
                best_pos = (max_loc[0] + tw // 2, max_loc[1] + th // 2)
        except Exception:
            continue
    return best_pos, best_conf


def click_at(pos, scale_x=1.0, scale_y=1.0):
    try:
        sx = int(round(pos[0] / max(1e-6, scale_x)))
        sy = int(round(pos[1] / max(1e-6, scale_y)))
        pyautogui.moveTo(sx, sy, duration=0.12)
        time.sleep(0.05)
        pyautogui.click(sx, sy)
    except Exception:
        pass


def test_alch_detection():
    print("\n🔮 Testing Alch Spell (TM multiscale over all templates)")
    print("-" * 40)

    templates = load_alch_templates()
    if not templates:
        print("❌ No alch spell templates found!")
        return None

    # Determine scaling (image vs OS coordinates)
    try:
        sw, sh = pyautogui.size()
        shot = pyautogui.screenshot()
        arr = np.array(shot)
        ih, iw = arr.shape[:2]
        scale_x = max(1e-6, iw / float(sw))
        scale_y = max(1e-6, ih / float(sh))
    except Exception:
        scale_x = scale_y = 1.0

    def detect_once():
        screenshot = pyautogui.screenshot()
        screen = np.array(screenshot)
        screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
        best_name, best_conf, best_pos = None, 0.0, None
        for name, (tmpl, path) in templates.items():
            pos, conf = multiscale_match(screen, tmpl)
            print(f"   {name} TM confidence: {conf:.3f}")
            if conf > best_conf and pos is not None:
                best_name, best_conf, best_pos = name, conf, pos
        if best_name:
            print(f"   🔮 Best match {best_name} via TM at {best_pos} (conf {best_conf:.3f})")
        else:
            print("   ❌ No match found on screen")
        return best_pos, best_conf

    # First attempt
    pos, conf = detect_once()
    if pos is None or conf < 0.68:
        print("❌ Not confidently found; pressing '3' to open spellbook")
        time.sleep(0.2)
        pyautogui.press('3')
        time.sleep(0.7)
        pos, conf = detect_once()

    if pos is not None and conf >= 0.68:
        print(f"✅ Clicking alch at {pos} (TM {conf:.3f})")
        click_at(pos, scale_x, scale_y)
        return pos
    else:
        print("❌ Could not confidently locate alch spell")
        return None


if __name__ == "__main__":
    print("Starting Alch Spell Detection Test...")
    print("Press Ctrl+C to stop")
    try:
        while True:
            test_alch_detection()
            print("\n" + "=" * 40)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")