#!/usr/bin/env python3
"""
Minimal orange tick reader: prints ONLY 1/2/3/4 when detected.

Run:
  python auto_actions/ticks/read_ticks_min.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

import cv2
import numpy as np
import pyautogui

# Make stdout safe
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
except Exception:
    pass


# Configure pytesseract (auto-find tesseract on Windows)
HAS_TESS = False
try:
    import pytesseract
    from shutil import which

    def _ensure_tesseract() -> bool:
        found = which("tesseract")
        if found and os.path.exists(found):
            return True
        envp = os.environ.get("TESSERACT_PATH")
        if envp and os.path.exists(envp):
            pytesseract.pytesseract.tesseract_cmd = envp
            return True
        user_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Tesseract-OCR", "tesseract.exe")
        for cand in [
            user_dir,
            r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
        ]:
            if os.path.exists(cand):
                pytesseract.pytesseract.tesseract_cmd = cand
                return True
        return False

    _ensure_tesseract()
    try:
        _ = pytesseract.get_tesseract_version()
        HAS_TESS = True
    except Exception:
        HAS_TESS = False
except ImportError:
    HAS_TESS = False


def capture() -> Optional[np.ndarray]:
    try:
        img = pyautogui.screenshot()
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def detect_digit(frame: np.ndarray) -> Optional[int]:
    # Use a center crop for speed; damage/timer digits are generally central
    h, w = frame.shape[:2]
    cx, cy = w // 2, h // 2
    m = 260
    crop = frame[max(0, cy - m):min(h, cy + m), max(0, cx - m):min(w, cx + m)]
    if crop.size == 0:
        return None

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    # Tight bright-orange bands (targeting ~FF7D00)
    ranges = [
        (np.array([20, 200, 220]), np.array([34, 255, 255])),
        (np.array([18, 170, 210]), np.array([36, 255, 255])),
    ]
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(hsv, lo, hi)

    if cv2.countNonZero(mask) < 40:
        return None

    # Clean up strokes
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    # Look at the biggest few blobs
    for c in sorted(contours, key=cv2.contourArea, reverse=True)[:6]:
        area = cv2.contourArea(c)
        if not (500 < area < 40000):
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        aspect = bh / float(max(bw, 1))
        if not (0.45 < aspect < 3.2):
            continue

        # Expand the bbox slightly and build a high-contrast glyph chip
        pad = int(max(bw, bh) * 0.35)
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(crop.shape[1], x + bw + pad)
        y1 = min(crop.shape[0], y + bh + pad)
        chip = crop[y0:y1, x0:x1]

        # Preprocess using the original colors (keep black outline), not the orange mask
        gray = cv2.cvtColor(chip, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        # Adaptive threshold to capture outline + fill
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 31, 2)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=1)
        proc = cv2.resize(th, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

        if HAS_TESS:
            # Try multiple OCR modes; stop at first valid digit
            for cfg in (
                '--oem 3 --psm 6 -c tessedit_char_whitelist=1234',
                '--oem 3 --psm 10 -c tessedit_char_whitelist=1234',
                '--oem 3 --psm 8 -c tessedit_char_whitelist=1234',
            ):
                try:
                    txt = pytesseract.image_to_string(proc, config=cfg).strip()
                except Exception:
                    txt = ''
                if txt.isdigit() and len(txt) == 1:
                    d = int(txt)
                    if 1 <= d <= 4:
                        return d

        # Heuristic fallback: tall slender blob often == '1'
        if aspect > 2.0 and area < 1400:
            return 1

    return None


def main():
    last_printed: Optional[int] = None
    confirm: Optional[int] = None
    confirm_hits = 0

    try:
        while True:
            frame = capture()
            if frame is None:
                time.sleep(0.03)
                continue
            d = detect_digit(frame)
            if d is None:
                confirm, confirm_hits = None, 0
            else:
                if confirm != d:
                    confirm, confirm_hits = d, 1
                else:
                    confirm_hits += 1
                # Print only after two consecutive frames agree
                if confirm_hits >= 2 and last_printed != confirm:
                    print(confirm)
                    last_printed = confirm
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


