#!/usr/bin/env python3
"""
Template-based detection utilities for OSRS orange countdown digits.

Exported:
- load_one_templates(templates_dir) -> list[np.ndarray]
- detect_one_from_frame(frame_bgr, one_templates, threshold=0.5) -> bool
- load_digit_templates(templates_dir, digit: str) -> list[np.ndarray]
- detect_digit_from_frame(frame_bgr, templates, threshold=0.5) -> bool
- load_all_templates(templates_dir) -> dict[str, list[np.ndarray]]
- classify_digit_from_frame(frame_bgr, templates_by_digit, scales=(0.6,0.8,1.0,1.2,1.4)) -> tuple[int|None, float]

These functions do no screen capture or I/O; they operate on a BGR frame.
"""

from __future__ import annotations

import os
from typing import List, Optional

import cv2
import numpy as np


def load_one_templates(templates_dir: str) -> List[np.ndarray]:
    """Load all template images whose filename starts with '1'.

    Returns binarized (white on black) grayscale images.
    """
    variants: List[np.ndarray] = []
    if not os.path.isdir(templates_dir):
        return variants
    for fname in sorted(os.listdir(templates_dir)):
        base, ext = os.path.splitext(fname)
        if not base.startswith("1") or ext.lower() not in (".png", ".jpg", ".jpeg", ".bmp"):
            continue
        path = os.path.join(templates_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, bin_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(bin_img)
    return variants


def load_digit_templates(templates_dir: str, digit: str) -> List[np.ndarray]:
    """Load all template images whose filename starts with the given digit ('1'..'4')."""
    variants: List[np.ndarray] = []
    if not os.path.isdir(templates_dir):
        return variants
    for fname in sorted(os.listdir(templates_dir)):
        base, ext = os.path.splitext(fname)
        if not base.startswith(str(digit)) or ext.lower() not in (".png", ".jpg", ".jpeg", ".bmp"):
            continue
        path = os.path.join(templates_dir, fname)
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, bin_img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variants.append(bin_img)
    return variants


def _orange_mask(bgr: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    lo1, hi1 = (10, 150, 170), (18, 255, 255)
    lo2, hi2 = (18, 130, 160), (36, 255, 255)
    m = cv2.inRange(hsv, np.array(lo1, np.uint8), np.array(hi1, np.uint8))
    m |= cv2.inRange(hsv, np.array(lo2, np.uint8), np.array(hi2, np.uint8))
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k, iterations=2)
    m = cv2.dilate(m, k, iterations=1)
    return m


def _digit_candidates(bgr: np.ndarray) -> list[np.ndarray]:
    """Return binarized candidate chips for digit classification (largest few)."""
    m = _orange_mask(bgr)
    h, w = m.shape
    # Trim HUD and chat
    m[: int(0.12 * h), :] = 0
    m[int(0.92 * h) :, :] = 0

    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    chips: list[np.ndarray] = []
    if not cnts:
        return chips
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:8]:
        area = cv2.contourArea(c)
        if not (300 < area < 50000):
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        aspect = bh / float(bw + 1e-5)
        # Allow slender '1' digits by extending upper bound
        if not (0.4 < aspect < 6.0):
            continue
        pad = 6
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(w, x + bw + pad), min(h, y + bh + pad)
        chip = bgr[y0:y1, x0:x1]
        chip_gray = cv2.cvtColor(chip, cv2.COLOR_BGR2GRAY)
        mask_crop = m[y0:y1, x0:x1]
        chip_bin = cv2.bitwise_and(chip_gray, chip_gray, mask=mask_crop)
        _, chip_bin = cv2.threshold(chip_bin, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        chips.append(chip_bin)
    return chips


def _matches_one(chip_bin: np.ndarray, one_templates: List[np.ndarray], threshold: float) -> bool:
    for scale in (0.7, 0.85, 1.0, 1.15, 1.3):
        rs = cv2.resize(chip_bin, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        rs_h, rs_w = rs.shape[:2]
        if rs_h < 6 or rs_w < 6:
            continue
        for tmpl in one_templates:
            th, tw = tmpl.shape[:2]
            t = tmpl
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


def detect_one_from_frame(frame_bgr: np.ndarray, one_templates: List[np.ndarray], threshold: float = 0.5) -> bool:
    """Return True if an orange '1' is detected in the frame."""
    candidates = _digit_candidates(frame_bgr)
    if not candidates:
        return False
    return any(_matches_one(ch, one_templates, threshold=threshold) for ch in candidates)


def detect_digit_from_frame(frame_bgr: np.ndarray, templates: List[np.ndarray], threshold: float = 0.5) -> bool:
    """Generic version for any digit templates (expects pre-binarized templates)."""
    candidates = _digit_candidates(frame_bgr)
    if not candidates:
        return False
    # Reuse matcher for convenience; templates content can be any digit
    return any(_matches_one(ch, templates, threshold=threshold) for ch in candidates)


def load_all_templates(templates_dir: str) -> dict[str, List[np.ndarray]]:
    """Load templates for digits '1'..'4'. Returns dict digit->list[bin_img]."""
    all_tmpls: dict[str, List[np.ndarray]] = {}
    for d in ("1", "2", "3", "4"):
        all_tmpls[d] = load_digit_templates(templates_dir, d)
    return all_tmpls


def classify_digit_from_frame(
    frame_bgr: np.ndarray,
    templates_by_digit: dict[str, List[np.ndarray]],
    scales: tuple[float, ...] = (0.6, 0.8, 1.0, 1.2, 1.4),
) -> tuple[Optional[int], float]:
    """Return (best_digit, best_score). best_digit is None if below threshold.

    This runs a multi-scale match across all digits and variants.
    """
    candidates = _digit_candidates(frame_bgr)
    if not candidates:
        return None, -1.0
    best_d: Optional[str] = None
    best_score = -1.0
    for chip in candidates:
        for scale in scales:
            rs = cv2.resize(chip, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
            rs_h, rs_w = rs.shape[:2]
            if rs_h < 6 or rs_w < 6:
                continue
            for d, tmpls in templates_by_digit.items():
                for tmpl in tmpls:
                    t = tmpl
                    th, tw = t.shape[:2]
                    if th > rs_h or tw > rs_w:
                        f = min(rs_h / float(th), rs_w / float(tw))
                        if f <= 0:
                            continue
                        t = cv2.resize(t, (max(1, int(tw * f)), max(1, int(th * f))), interpolation=cv2.INTER_NEAREST)
                    try:
                        score = float(cv2.matchTemplate(rs, t, cv2.TM_CCOEFF_NORMED).max())
                    except cv2.error:
                        continue
                    if score > best_score:
                        best_score, best_d = score, d
    return (int(best_d) if best_d is not None else None), best_score


