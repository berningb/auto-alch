#!/usr/bin/env python3
"""
Minimal Tick Number Detector (1..4)

- Captures the screen and looks for the big bold orange tick number above the player
- Prints ONLY the detected number (1, 2, 3, or 4) when it changes
  No flicking, no extra logs

Hotkeys:
  p = pause/resume
  q = quit
  c = set ROI around mouse (100px margin)
  x = clear ROI (use center crop)
  f = toggle full-screen vs center crop search
  d = toggle debug (optional)

Run:
  python auto_actions/ticks/tick_detector_test.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

import cv2
import numpy as np
import pyautogui

# Local imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTO_ACTIONS_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(AUTO_ACTIONS_DIR)

try:
    from pynput import keyboard
    from funcs import AutoActionFunctions
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# OCR availability and tesseract path
HAS_TESS = False
try:
    import pytesseract
    from shutil import which

    def _ensure_tesseract_path() -> bool:
        found = which("tesseract")
        if found and os.path.exists(found):
            return True
        env_path = os.environ.get("TESSERACT_PATH")
        if env_path and os.path.exists(env_path):
            pytesseract.pytesseract.tesseract_cmd = env_path
            return True
        user_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe")
        candidates = [
            user_dir,
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]
        for c in candidates:
            if os.path.exists(c):
                pytesseract.pytesseract.tesseract_cmd = c
                return True
        return False

    _ensure_tesseract_path()
    try:
        ver = pytesseract.get_tesseract_version()
        HAS_TESS = True
        # Quiet success
    except Exception:
        HAS_TESS = False
except ImportError:
    HAS_TESS = False


# HSV ranges tuned for OSRS bold orange
HSV_ORANGE_RANGES = [
    (np.array([20, 200, 200]), np.array([35, 255, 255])),
    (np.array([16, 160, 160]), np.array([40, 255, 255])),
]

PAUSED = True
STOP = False
DEBUG = False
CUSTOM_ROI: Optional[tuple[int, int, int, int]] = None
FULL_SCAN = False


def on_key_press(key):
    global PAUSED, STOP, CUSTOM_ROI, DEBUG, FULL_SCAN
    try:
        if key.char == 'p':
            PAUSED = not PAUSED
            print("▶️" if not PAUSED else "⏸️")
        elif key.char == 'q':
            STOP = True
            return False
        elif key.char == 'c':
            x, y = pyautogui.position()
            m = 100
            CUSTOM_ROI = (x - m, y - m, x + m, y + m)
        elif key.char == 'x':
            CUSTOM_ROI = None
        elif key.char == 'd':
            DEBUG = not DEBUG
        elif key.char == 'f':
            FULL_SCAN = not FULL_SCAN
    except AttributeError:
        pass


def detect_tick(frame: np.ndarray) -> Optional[int]:
    # Choose ROI
    if CUSTOM_ROI:
        x1, y1, x2, y2 = CUSTOM_ROI
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)
        roi = frame[y1:y2, x1:x2]
        offset = (x1, y1)
    else:
        if FULL_SCAN:
            roi = frame
            offset = (0, 0)
        else:
            h, w = frame.shape[:2]
            cx, cy = w // 2, h // 2
            margin = 180
            roi = frame[max(0, cy - margin): cy + margin, max(0, cx - margin): cx + margin]
            offset = (max(0, cx - margin), max(0, cy - margin))

    if roi.size == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in HSV_ORANGE_RANGES:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lo, hi))

    if cv2.countNonZero(mask) < 20:
        return None

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best_digit = None
    for c in contours:
        area = cv2.contourArea(c)
        if 40 < area < 5000:
            x, y, w, h = cv2.boundingRect(c)
            aspect = h / float(max(w, 1))
            if 0.4 < aspect < 4.5:
                # OCR preprocess
                crop = roi[y:y+h, x:x+w]
                m = mask[y:y+h, x:x+w]
                masked = cv2.bitwise_and(crop, crop, mask=m)
                gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
                _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                proc = th if np.mean(th) > 127 else cv2.bitwise_not(th)
                proc = cv2.dilate(proc, np.ones((2, 2), np.uint8), iterations=1)
                proc = cv2.resize(proc, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

                if HAS_TESS:
                    try:
                        txt = pytesseract.image_to_string(
                            proc, config='--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
                        ).strip()
                        if txt.isdigit() and len(txt) == 1:
                            d = int(txt)
                            if 0 <= d <= 4:
                                best_digit = d
                                break
                    except Exception:
                        pass
                # Heuristic for slender tall contour as '1'
                if best_digit is None and aspect > 2.0 and area < 800:
                    best_digit = 1
                    break
    return best_digit


def main():
    print("Tick Number Detector (prints only 1/2/3/4 when detected)")
    print("Hotkeys: p=pause/resume, q=quit, c=set ROI, x=clear ROI, f=toggle full-screen, d=debug")
    print("⏸️  PAUSED - Press 'p' to start")

    funcs = AutoActionFunctions()
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    last_digit = None
    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue

            frame = funcs.capture_screen()
            if frame is None:
                time.sleep(0.05)
                continue

            digit = detect_tick(frame)
            if digit is not None and digit != last_digit:
                print(f"{digit}")
                last_digit = digit

            time.sleep(0.05)
    finally:
        listener.stop()


if __name__ == "__main__":
    main()


