#!/usr/bin/env python3
"""
Detect only the orange tick '1' via color mask + template matching.

Prints exactly: "1 detected" when a stable match is found.

Templates directory: auto_actions/ticks/templates/
 - Add multiple variants that start with '1' (e.g., 1.png, 1-white.png, 1a.png)

Run:
  python auto_actions/ticks/read_one_tm.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import List, Optional

import cv2
import numpy as np


# ---- Template loading (only those starting with '1') ----
def load_one_templates(templates_dir: str) -> List[np.ndarray]:
    variants: List[np.ndarray] = []
    if not os.path.isdir(templates_dir):
        return variants
    for fname in sorted(os.listdir(templates_dir)):
        base, ext = os.path.splitext(fname)
        if not base.startswith('1') or ext.lower() not in ('.png', '.jpg', '.jpeg', '.bmp'):
            continue
        path = os.path.join(templates_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, bin_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(bin_img)
    return variants


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
ONE_TEMPLATES = load_one_templates(TEMPLATES_DIR)
if not ONE_TEMPLATES:
    print(f"❌ No '1' templates found in {TEMPLATES_DIR}. Add files like 1.png, 1-white.png")
    sys.exit(1)


# ---- Capture (prefer mss) ----
try:
    from mss import mss  # type: ignore

    _grab = mss()
    _mon = _grab.monitors[1]

    def capture_bgr() -> np.ndarray:
        img = np.asarray(_grab.grab(_mon))
        return img[:, :, :3][:, :, ::-1]

except Exception:
    import pyautogui  # type: ignore

    def capture_bgr() -> np.ndarray:
        shot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)


# ---- Orange mask (broad but biased to bright orange) ----
def orange_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lo1, hi1 = (10, 150, 170), (18, 255, 255)
    lo2, hi2 = (18, 130, 160), (36, 255, 255)
    m = cv2.inRange(hsv, np.array(lo1, np.uint8), np.array(hi1, np.uint8))
    m |= cv2.inRange(hsv, np.array(lo2, np.uint8), np.array(hi2, np.uint8))
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    m = cv2.dilate(m, k, iterations=1)
    return m


def best_digit_chip(bgr: np.ndarray) -> Optional[np.ndarray]:
    m = orange_mask(bgr)
    h, w = m.shape
    # Trim HUD and chat a bit
    m[: int(0.12 * h), :] = 0
    m[int(0.92 * h) :, :] = 0

    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:6]:
        area = cv2.contourArea(c)
        if not (500 < area < 40000):
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        aspect = bh / float(bw + 1e-5)
        if not (0.5 < aspect < 3.8):
            continue
        pad = 6
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(w, x + bw + pad), min(h, y + bh + pad)
        chip = bgr[y0:y1, x0:x1]
        chip_gray = cv2.cvtColor(chip, cv2.COLOR_BGR2GRAY)
        mask_crop = m[y0:y1, x0:x1]
        chip_bin = cv2.bitwise_and(chip_gray, chip_gray, mask=mask_crop)
        _, chip_bin = cv2.threshold(chip_bin, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return chip_bin
    return None


def matches_one(chip_bin: np.ndarray, threshold: float = 0.5) -> bool:
    # Try multiple scales and all 1-templates; succeed if any score exceeds threshold
    for scale in (0.7, 0.85, 1.0, 1.15, 1.3):
        rs = cv2.resize(chip_bin, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        rs_h, rs_w = rs.shape[:2]
        if rs_h < 6 or rs_w < 6:
            continue
        for tmpl in ONE_TEMPLATES:
            th, tw = tmpl.shape[:2]
            t = tmpl
            # ensure template fits inside the image
            if th > rs_h or tw > rs_w:
                f = min(rs_h / float(th), rs_w / float(tw))
                if f <= 0:
                    continue
                t = cv2.resize(t, (max(1, int(tw * f)), max(1, int(th * f))), interpolation=cv2.INTER_NEAREST)
            try:
                score = float(cv2.matchTemplate(rs, t, cv2.TM_CCOEFF_NORMED).max())
            except cv2.error:
                continue
            if score >= threshold:
                return True
    return False


def main():
    last_printed = False
    confirm = 0
    cooldown_until = 0.0

    try:
        while True:
            frame = capture_bgr()
            chip = best_digit_chip(frame)
            now = time.time()
            if chip is not None and matches_one(chip, threshold=0.50):
                if now >= cooldown_until:
                    confirm += 1
                    if confirm >= 2 and not last_printed:
                        print("1 detected", flush=True)
                        last_printed = True
                        cooldown_until = now + 0.25
                else:
                    # in cooldown, keep state but don't spam
                    last_printed = True
            else:
                confirm = 0
                last_printed = False
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


