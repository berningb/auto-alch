#!/usr/bin/env python3
"""
Orange Tick Reader (template version) — prints 1..4 when it changes

Usage:
  - Place digit templates under auto_actions/ticks/templates/
    e.g. templates/1.png, templates/2.png, templates/3.png, templates/4.png
    (cropped white-on-black after thresholding works best)

  - Run: python auto_actions/ticks/read_ticks_tm.py

Notes:
  - Prefers mss for fast capture; falls back to pyautogui if not installed
  - Only prints the detected digit when it changes
"""

from __future__ import annotations

import os
import sys
import time
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np


# --- load templates (binarized) ---
def load_templates(templates_dir: str) -> Dict[str, List[np.ndarray]]:
    templates: Dict[str, List[np.ndarray]] = {"1": [], "2": [], "3": [], "4": []}
    # Support multiple variants per digit: 1.png, 1a.png, 1_2.png, etc.
    for d in ("1", "2", "3", "4"):
        variants = []
        for name in os.listdir(templates_dir) if os.path.isdir(templates_dir) else []:
            pass
        # Safer manual scan to respect case and suffixes
        for fname in sorted(os.listdir(templates_dir)) if os.path.isdir(templates_dir) else []:
            base, ext = os.path.splitext(fname)
            if ext.lower() not in (".png", ".jpg", ".jpeg", ".bmp"):
                continue
            if not base.startswith(d):
                continue
            path = os.path.join(templates_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            # Binarize for robust matching
            _, bin_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            variants.append(bin_img)
        if not variants:
            # Also try the strict single filename (d.png)
            strict = os.path.join(templates_dir, f"{d}.png")
            img = cv2.imread(strict, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                _, bin_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                variants.append(bin_img)
        templates[d] = variants
    return templates


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
TEMPLATES = load_templates(TEMPLATES_DIR)
MISSING = [d for d, arr in TEMPLATES.items() if not arr]
if MISSING:
    print(f"❌ Missing templates for digits: {', '.join(MISSING)} in {TEMPLATES_DIR}")
    print("   Add images: 1.png, 2.png, 3.png, 4.png (optionally multiple variants per digit)")
    sys.exit(1)


# --- capture (mss is much faster than pyautogui) ---
try:
    from mss import mss  # type: ignore

    _grabber = mss()
    _monitor = _grabber.monitors[1]

    def capture_bgr() -> np.ndarray:
        img = np.asarray(_grabber.grab(_monitor))
        return img[:, :, :3][:, :, ::-1]  # BGRA->BGR

except Exception:
    import pyautogui  # type: ignore

    def capture_bgr() -> np.ndarray:
        shot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)


# --- color mask tuned for “big orange” (HD plugin friendly) ---
def orange_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    # broaden hue a bit; V high; S high
    lo1, hi1 = (10, 150, 170), (18, 255, 255)
    lo2, hi2 = (18, 130, 160), (36, 255, 255)
    m = cv2.inRange(hsv, np.array(lo1, dtype=np.uint8), np.array(hi1, dtype=np.uint8))
    m |= cv2.inRange(hsv, np.array(lo2, dtype=np.uint8), np.array(hi2, dtype=np.uint8))
    # clean it up
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    m = cv2.dilate(m, k, iterations=1)
    return m


# --- pick the best orange blob that looks like a digit ---
def best_digit_chip(bgr: np.ndarray) -> Optional[np.ndarray]:
    m = orange_mask(bgr)

    # ignore top HUD & chat areas to dodge UI bars (tweak as needed)
    h, w = m.shape
    m[: int(0.12 * h), :] = 0
    m[int(0.92 * h) :, :] = 0

    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    for c in cnts[:6]:
        area = cv2.contourArea(c)
        if not (500 < area < 40000):  # heuristics to skip tiny leaves / huge bars
            continue
        x, y, w_, h_ = cv2.boundingRect(c)
        aspect = h_ / float(w_ + 1e-5)
        if not (0.5 < aspect < 3.8):
            continue
        pad = 6
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(w, x + w_ + pad), min(h, y + h_ + pad)
        chip = bgr[y0:y1, x0:x1]
        # binarize chip from mask for stable matching
        chip_gray = cv2.cvtColor(chip, cv2.COLOR_BGR2GRAY)
        mask_crop = m[y0:y1, x0:x1]
        chip_bin = cv2.bitwise_and(chip_gray, chip_gray, mask=mask_crop)
        _, chip_bin = cv2.threshold(chip_bin, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return chip_bin
    return None


# --- multi-scale template match across 1..4 ---
def classify_digit(chip_bin: np.ndarray) -> Optional[int]:
    best_d: Optional[str] = None
    best_score: float = -1.0
    # normalize chip size range so we don’t miss larger/smaller splats
    for scale in (0.6, 0.8, 1.0, 1.2, 1.4):
        rs = cv2.resize(chip_bin, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        rs_h, rs_w = rs.shape[:2]
        if rs_h < 6 or rs_w < 6:
            continue
        for d, tmpls in TEMPLATES.items():
            for tmpl in tmpls:
                t = tmpl
                th, tw = t.shape[:2]
                # Ensure template fits inside image
                if th > rs_h or tw > rs_w:
                    factor = min(rs_h / float(th), rs_w / float(tw))
                    if factor <= 0:
                        continue
                    new_w = max(1, int(tw * factor))
                    new_h = max(1, int(th * factor))
                    t = cv2.resize(t, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
                try:
                    res = cv2.matchTemplate(rs, t, cv2.TM_CCOEFF_NORMED)
                    score = float(res.max())
                except cv2.error:
                    continue
                if score > best_score:
                    best_score, best_d = score, d
    # empirical threshold; adjust if needed
    return int(best_d) if (best_d is not None and best_score > 0.45) else None


def main():
    last: Optional[int] = None
    try:
        while True:
            frame = capture_bgr()
            chip = best_digit_chip(frame)
            if chip is not None:
                d = classify_digit(chip)
                if d is not None and d != last:
                    print(d, flush=True)
                    last = d
            time.sleep(0.04)  # ~25 FPS loop
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()


