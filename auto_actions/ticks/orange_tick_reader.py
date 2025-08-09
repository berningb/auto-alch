#!/usr/bin/env python3
"""
Orange Tick Reader (prints only 1,2,3,4)

Continuously captures the screen, isolates BRIGHT orange glyphs,
OCRs a single character, and prints the digit when it changes.

No hotkeys, no extra logs.

Run:
  python auto_actions/ticks/orange_tick_reader.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui

# Make stdout unicode-tolerant on Windows consoles
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
except Exception:
    pass


# Locate tesseract for pytesseract
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
        for c in [
            user_dir,
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]:
            if os.path.exists(c):
                pytesseract.pytesseract.tesseract_cmd = c
                return True
        return False

    _ensure_tesseract_path()
    try:
        _ = pytesseract.get_tesseract_version()
        HAS_TESS = True
    except Exception:
        HAS_TESS = False
except ImportError:
    HAS_TESS = False


def capture_screen_bgr() -> Optional[np.ndarray]:
    try:
        img = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return frame
    except Exception:
        return None


def find_orange_digit(frame: np.ndarray) -> Optional[int]:
    # BRIGHT orange thresholds (tuned for OSRS damage/timer orange)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Combine a couple of tight bright-orange bands for robustness
    ranges = [
        (np.array([20, 200, 220]), np.array([33, 255, 255])),
        (np.array([18, 180, 210]), np.array([36, 255, 255])),
    ]
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lo, hi))

    if cv2.countNonZero(mask) < 30:
        return None

    # Morphology to solidify strokes
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Focus on the largest bright-orange blob(s)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    for c in contours[:6]:
        area = cv2.contourArea(c)
        if not (400 < area < 30000):  # large but not full UI bars
            continue
        x, y, w, h = cv2.boundingRect(c)
        aspect = h / float(max(w, 1))
        if not (0.5 < aspect < 3.5):
            continue

        # Build a clean OCR chip
        crop = frame[y:y + h, x:x + w]
        m = mask[y:y + h, x:x + w]
        masked = cv2.bitwise_and(crop, crop, mask=m)
        gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        proc = th if np.mean(th) > 127 else cv2.bitwise_not(th)
        proc = cv2.dilate(proc, np.ones((2, 2), np.uint8), iterations=1)
        proc = cv2.resize(proc, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

        # OCR single glyph 1..4 only
        if HAS_TESS:
            try:
                txt = pytesseract.image_to_string(
                    proc,
                    config='--oem 3 --psm 10 -c tessedit_char_whitelist=1234'
                ).strip()
                if txt.isdigit() and len(txt) == 1:
                    d = int(txt)
                    if 1 <= d <= 4:
                        return d
            except Exception:
                pass

        # Heuristic: very slender tall blob often equals '1'
        if aspect > 2.0 and area < 1200:
            return 1

    return None


def main():
    last = None
    try:
        while True:
            frame = capture_screen_bgr()
            if frame is None:
                time.sleep(0.05)
                continue
            d = find_orange_digit(frame)
            if d is not None and d != last:
                print(d)
                last = d
            time.sleep(0.06)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


