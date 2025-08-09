#!/usr/bin/env python3
"""
Attack Flicker

Detect the orange attack timer (bar + digit) above the player and flick
Quick-prayer when the countdown shows the target tick value (default 2).

Hotkeys:
- p: pause / resume
- q: quit
- 0..4: set target tick value (e.g., press '2' to flick at 2 ticks)

Requirements:
- Uses color detection (HSV) to isolate the orange UI elements
- Optionally uses pytesseract to OCR the digit (falls back to heuristics)

Run:
  python watchers/auto_actions/ticks/attack_flicker.py
"""

from __future__ import annotations

import os
import sys
import time
import random
from typing import Optional, Tuple

import cv2
import numpy as np
import pyautogui

# Add auto_actions to path for AutoActionFunctions
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTO_ACTIONS_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(AUTO_ACTIONS_DIR)
sys.path.append(CURRENT_DIR)

# Make stdout tolerant to emojis/unicode on Windows consoles
try:  # Python 3.7+
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='ignore')  # type: ignore
    except Exception:
        pass

try:
    from pynput import keyboard
    from funcs import AutoActionFunctions
    # Template-based '1' detector (no OCR)
    from tm_detect import (
        load_one_templates,
        detect_one_from_frame,
        load_digit_templates,
        detect_digit_from_frame,
    )
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Try to import OCR for digit detection and ensure tesseract binary is located
HAS_TESS = False
try:
    import pytesseract
    from shutil import which

    def _ensure_tesseract_path() -> bool:
        """Best-effort attempt to point pytesseract at the Tesseract binary on Windows.

        Returns True if a usable tesseract executable is found.
        """
        # If already discoverable via PATH, prefer that
        found = which("tesseract")
        if found and os.path.exists(found):
            return True

        # Environment override
        env_path = os.environ.get("TESSERACT_PATH")
        if env_path and os.path.exists(env_path):
            pytesseract.pytesseract.tesseract_cmd = env_path
            return True

        # Common Windows install locations
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

    # Try to ensure path and verify version
    _ensure_tesseract_path()
    try:
        ver = pytesseract.get_tesseract_version()
        HAS_TESS = True
        print(f"✅ OCR ready - Tesseract {ver}")
    except Exception as _e:
        HAS_TESS = False
        print("⚠️ pytesseract installed but Tesseract binary not found. Set PATH or configure tesseract_cmd.")
        print("   Tip: Install from 'UB-Mannheim Tesseract' and ensure its folder is in PATH.")
except ImportError:
    HAS_TESS = False
    print("⚠️ OCR not available - install pytesseract for digit detection")


# Broad HSV ranges for OSRS-style orange UI elements.
# We OR multiple ranges to be robust across monitors/post-processing.
HSV_ORANGE_RANGES = [
    (np.array([5, 80, 100]), np.array([25, 255, 255])),   # classic orange
    (np.array([15, 40, 180]), np.array([35, 255, 255])),  # lighter/amber
]


PAUSED = True
STOP = False
TARGET_TICK = 2
DEBUG = False  # minimal logging by default; toggle with 'd'
FULL_SCAN = False  # if True, scan whole screen instead of center crop
CUSTOM_ROI = None  # (x1, y1, x2, y2) if user sets a manual region
OFFSET_MS = 140  # delay after detecting target tick before flicking
STABILITY_FRAMES = 2  # require consecutive confirmations before scheduling
USE_OCR_MODE = True  # if True, use OCR detection; if False, use pure timing
DETECTION_MODE = True  # if True, sync to detected ticks; if False, pure 1-tick mode
# Template mode to detect orange digits via templates
USE_TEMPLATE_ONE = True   # detect '1' for logging/diagnostics
USE_TEMPLATE_TWO = True   # detect '2' to toggle ON and '4' to toggle OFF
PRE_DELAY_MS: Optional[float] = 40.0  # default small delay after '1' (ms)
MIN_COOLDOWN_MS = 200                 # minimum ms between flicks to prevent double fire


def on_key_press(key):
    global PAUSED, STOP, TARGET_TICK, OFFSET_MS, TICK_MS, SYNCED, next_flick_ms, cycle_start_ms
    global DEBUG, CUSTOM_ROI, USE_OCR_MODE, DETECTION_MODE
    try:
        if key.char == 'p':
            PAUSED = not PAUSED
            print("▶️  RUNNING" if not PAUSED else "⏸️  PAUSED")
        elif key.char == 'q':
            STOP = True
            print("🛑 QUIT requested")
            return False
        elif key.char in ('0', '1', '2', '3', '4'):
            TARGET_TICK = int(key.char)
            print(f"🎯 target tick = {TARGET_TICK}")
        elif key.char == 'd':
            DEBUG = not DEBUG
            print(f"🐛 Debug mode: {'ON' if DEBUG else 'OFF'}")
        elif key.char == 'c':
            # Set ROI - user should position mouse near the countdown timer
            x, y = pyautogui.position()
            margin = 50
            CUSTOM_ROI = (x - margin, y - margin, x + margin, y + margin)
            print(f"📍 Set detection ROI: {CUSTOM_ROI} (around mouse position)")
        elif key.char == 'x':
            CUSTOM_ROI = None
            print("🗑️ Cleared ROI - will scan center area")
        elif key.char == 'o':
            USE_OCR_MODE = not USE_OCR_MODE
            print(f"👁️ OCR mode: {'ON' if USE_OCR_MODE else 'OFF'}")
        elif key.char == 'm':
            DETECTION_MODE = not DETECTION_MODE
            print(f"🎯 Detection mode: {'SYNC' if DETECTION_MODE else 'PURE_TIMING'}")
        elif key.char == 'f':
            global FULL_SCAN
            FULL_SCAN = not FULL_SCAN
            print(f"🖼️ Search area: {'FULL SCREEN' if FULL_SCAN else 'CENTER ROI'}")
        
    except AttributeError:
        pass


def detect_orange_digit(frame):
    """Detect orange countdown digit using OCR and color filtering."""
    try:
        # Get ROI
        if CUSTOM_ROI:
            x1, y1, x2, y2 = CUSTOM_ROI
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(frame.shape[1], x2), min(frame.shape[0], y2)
            roi = frame[y1:y2, x1:x2]
            if DEBUG:
                print(f"🔍 Using custom ROI: {CUSTOM_ROI}")
        else:
            # Either scan full screen or a center crop
            if FULL_SCAN:
                roi = frame
                if DEBUG:
                    print("🔍 Using FULL SCREEN ROI")
            else:
                # Default to center area where timer usually appears
                h, w = frame.shape[:2]
                cx, cy = w // 2, h // 2
                margin = 180  # slightly larger search area
                roi = frame[max(0, cy-margin):cy+margin, max(0, cx-margin):cx+margin]
                if DEBUG:
                    print(f"🔍 Using center ROI: {cx-margin},{cy-margin} to {cx+margin},{cy+margin}")
        
        if roi.size == 0:
            if DEBUG:
                print("⚠️ ROI is empty")
            return None
            
        # Convert to HSV for orange detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Debug: Show HSV range in ROI
        if DEBUG:
            h_min, h_max = hsv[:,:,0].min(), hsv[:,:,0].max()
            s_min, s_max = hsv[:,:,1].min(), hsv[:,:,1].max() 
            v_min, v_max = hsv[:,:,2].min(), hsv[:,:,2].max()
            print(f"🎨 HSV ranges in ROI - H:[{h_min}-{h_max}] S:[{s_min}-{s_max}] V:[{v_min}-{v_max}]")
        
        # Create mask for orange colors - targeting FF7D00 specifically
        orange_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        # FF7D00 = RGB(255, 125, 0) converts to HSV(~29, 255, 255)
        # Add ranges around this specific color
        expanded_ranges = [
            (np.array([25, 200, 200]), np.array([35, 255, 255])),  # Target FF7D00 range
            (np.array([20, 150, 150]), np.array([40, 255, 255])),  # Wider orange range
            (np.array([15, 100, 100]), np.array([45, 255, 255])),  # Even wider for variations
        ]
        
        for lower, upper in expanded_ranges:
            mask_range = cv2.inRange(hsv, lower, upper)
            orange_mask = cv2.bitwise_or(orange_mask, mask_range)
        
        # Count orange pixels for debugging
        orange_pixels = cv2.countNonZero(orange_mask)
        if DEBUG:
            print(f"🟠 Found {orange_pixels} orange pixels")
        
        if orange_pixels < 20:  # Not enough orange detected
            return None
        
        # Find contours for digit-like shapes
        contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if DEBUG:
            print(f"🔍 Found {len(contours)} contours")
        
        best_digit = None
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if DEBUG:
                print(f"  Contour {i}: area={area}")
            
            if 30 < area < 3000:  # More lenient size filter
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                if DEBUG:
                    print(f"  Contour {i}: bbox=({x},{y},{w},{h}), aspect={aspect_ratio:.2f}")
                
                if 0.5 < aspect_ratio < 4.0:  # More lenient aspect ratio
                    # Build a masked color crop for OCR
                    color_crop = roi[y:y+h, x:x+w]
                    mask_crop = orange_mask[y:y+h, x:x+w]
                    masked = cv2.bitwise_and(color_crop, color_crop, mask=mask_crop)

                    # Preprocess for OCR
                    gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (3, 3), 0)
                    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    # Ensure dark text on white background for Tesseract
                    proc = th if np.mean(th) > 127 else cv2.bitwise_not(th)
                    # Slight dilation to connect strokes
                    kernel = np.ones((2, 2), np.uint8)
                    proc = cv2.dilate(proc, kernel, iterations=1)
                    # Scale up for better OCR
                    proc = cv2.resize(proc, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST)

                    if HAS_TESS:
                        # OCR configuration for single digits
                        config = '--oem 3 --psm 10 -c tessedit_char_whitelist=0123456789'
                        try:
                            text = pytesseract.image_to_string(proc, config=config).strip()
                            if DEBUG:
                                print(f"  OCR result: '{text}'")

                            if text.isdigit() and len(text) == 1:
                                digit = int(text)
                                if 0 <= digit <= 4:  # Valid attack countdown range
                                    best_digit = digit
                                    break
                        except Exception as ocr_err:
                            if DEBUG:
                                print(f"  OCR error: {ocr_err}")
                    else:
                        # Fallback: template matching or pixel analysis
                        if DEBUG:
                            print("  No OCR available, using fallback")
                        # Simple heuristic: if we found orange pixels in digit shape, assume it's valid
                        # You could add template matching here for digits 0-4
                        best_digit = 1  # Default assumption for testing

                    # Heuristic fallback for a very slender digit likely to be '1'
                    if best_digit is None and aspect_ratio > 2.0 and area < 600:
                        best_digit = 1
                        if DEBUG:
                            print("  Heuristic: interpreting slender contour as '1'")
        
        if DEBUG and best_digit is not None:
            print(f"🎯 Final detected digit: {best_digit}")
        
        return best_digit
        
    except Exception as e:
        if DEBUG:
            print(f"⚠️ Detection error: {e}")
        return None


def main():
    print("Hotkeys: p=pause/resume, q=quit, c=set ROI near timer, x=clear ROI, d=debug, o=toggle OCR, m=toggle detection mode")
    print("⏸️  PAUSED - Press 'p' to start")

    funcs = AutoActionFunctions()
    if not funcs.qp_center:
        print("⚠️ No quick-prayer calibration found. Run qp_calibrate.py for best reliability.")
    # Detection/sync not required for pure 1-tick flick mode

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    global TICK_MS, SYNCED, cycle_start_ms, next_flick_ms, PRE_DELAY_MS
    last_trigger_ts = 0.0
    last_detected_digit = None
    stability_counter = 0
    TICK_MS = 616  # OSRS game tick duration in ms (approx)
    SYNCED = False
    cycle_start_ms = None
    next_flick_ms = None
    if DEBUG:
        print(f"OCR Detection mode: flick when countdown hits 1")
    if DEBUG:
        print(f"Detection mode: {DETECTION_MODE}, OCR mode: {USE_OCR_MODE}, Debug: {DEBUG}")

    # Load '1' templates for template-based detection
    global USE_TEMPLATE_ONE, USE_TEMPLATE_TWO
    one_templates = []
    two_templates = []
    four_templates = []
    if USE_TEMPLATE_ONE or USE_TEMPLATE_TWO:
        try:
            templates_dir = os.path.join(CURRENT_DIR, "templates")
            if USE_TEMPLATE_ONE:
                one_templates = load_one_templates(templates_dir)
                if one_templates:
                    print(f"✅ Loaded {len(one_templates)} '1' templates")
                else:
                    print("⚠️ No '1' templates found; disabling '1' detection")
                    USE_TEMPLATE_ONE = False
            if USE_TEMPLATE_TWO:
                two_templates = load_digit_templates(templates_dir, digit='2')
                four_templates = load_digit_templates(templates_dir, digit='4')
                if two_templates:
                    print(f"✅ Loaded {len(two_templates)} '2' templates")
                else:
                    print("⚠️ No '2' templates found; disabling '2' detection")
                    USE_TEMPLATE_TWO = False
                if four_templates:
                    print(f"✅ Loaded {len(four_templates)} '4' templates")
        except Exception as e:
            print(f"⚠️ Failed to load '1' templates: {e}")
            USE_TEMPLATE_ONE = False
            USE_TEMPLATE_TWO = False

    # Load pre-delay from recorded data if available (based on digit 1)
    try:
        data_csv = os.path.join(os.path.dirname(CURRENT_DIR), 'data', 'click_timing.csv')
        if os.path.exists(data_csv):
            import csv, statistics
            deltas = []
            with open(data_csv, 'r', newline='') as f:
                r = csv.DictReader(f)
                for row in r:
                    if row.get('digit') == '1' and row.get('ms_since_last_digit_change'):
                        try:
                            deltas.append(float(row['ms_since_last_digit_change']))
                        except Exception:
                            pass
            if deltas:
                med = statistics.median(deltas)
                PRE_DELAY_MS = max(0.0, med - 10.0)
                print(f"🧪 Learned pre-delay for '1': ~{int(PRE_DELAY_MS)} ms (median-10ms)")
            elif PRE_DELAY_MS is not None:
                print(f"🧪 Using default pre-delay for '1': {int(PRE_DELAY_MS)} ms")
    except Exception as _e:
        pass

    try:
        scheduled_flick_ms = None
        # Tick cadence estimator
        tick_ms_estimate: float = 616.0
        last_change_ms: Optional[float] = None
        intervals: list[float] = []
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue

            now = time.time() * 1000.0
            prev_digit = last_detected_digit

            # Capture screen for detection
            if DETECTION_MODE and (USE_OCR_MODE or USE_TEMPLATE_ONE or USE_TEMPLATE_TWO):
                if DEBUG:
                    print("📸 Capturing screen for detection...")
                frame = funcs.capture_screen()
                if frame is not None:
                    if DEBUG:
                        print(f"📸 Screen captured: {frame.shape}")
                    detected_digit = None
                    # Detect '2'/'4' first for toggling logic (template-based)
                    if USE_TEMPLATE_TWO and two_templates:
                        try:
                            if detect_digit_from_frame(frame, two_templates, threshold=0.50):
                                detected_digit = 2
                        except Exception:
                            pass
                    if detected_digit is None and USE_TEMPLATE_TWO and four_templates:
                        try:
                            if detect_digit_from_frame(frame, four_templates, threshold=0.50):
                                detected_digit = 4
                        except Exception:
                            pass
                    # Optional '1' for logging only
                    if detected_digit is None and USE_TEMPLATE_ONE and one_templates:
                        try:
                            if detect_one_from_frame(frame, one_templates, threshold=0.50):
                                detected_digit = 1
                        except Exception:
                            pass
                    # Fallback to OCR for other digits if enabled
                    if detected_digit is None and USE_OCR_MODE:
                        detected_digit = detect_orange_digit(frame)
                    
                    # Update tick estimator on any digit change
                    if detected_digit != prev_digit and detected_digit is not None:
                        if last_change_ms is not None:
                            dt = now - last_change_ms
                            if 300.0 <= dt <= 900.0:  # plausible OSRS tick
                                intervals.append(dt)
                                if len(intervals) > 8:
                                    intervals.pop(0)
                                tick_ms_estimate = sum(intervals) / len(intervals)
                        last_change_ms = now

                    # Toggle ON when '2' appears; OFF when '4' appears
                    if detected_digit == 2 and prev_digit != 2 and (now - last_trigger_ts) > MIN_COOLDOWN_MS:
                        ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=50, settle_ms_max=100, hold_ms_min=55, hold_ms_max=90)
                        if ok:
                            print("⚡ Toggle ON (2)")
                            last_trigger_ts = now
                    if detected_digit == 4 and prev_digit != 4 and (now - last_trigger_ts) > MIN_COOLDOWN_MS:
                        ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=50, settle_ms_max=100, hold_ms_min=55, hold_ms_max=90)
                        if ok:
                            print("⚡ Toggle OFF (4)")
                            last_trigger_ts = now
                    
                    # Log only when digit changes and we actually know the digit
                    if detected_digit != prev_digit and detected_digit is not None:
                        print(f"{detected_digit}")
                    # Update last seen (including None to allow re-trigger)
                    last_detected_digit = detected_digit
            
            else:
                # Fallback: pure timing mode (flick every tick)
                if next_flick_ms is not None and now >= next_flick_ms:
                    ok = funcs.pray_tick(
                        use_mouse=True,
                        min_gap_ms=45,
                        max_gap_ms=75,
                        settle_ms_min=30,
                        settle_ms_max=50,
                        hold_on_ms_min=40,
                        hold_on_ms_max=70,
                        hold_off_ms_min=40,
                        hold_off_ms_max=70,
                    )
                    last_trigger_ts = now
                    next_flick_ms += TICK_MS
                    while next_flick_ms <= now:
                        next_flick_ms += TICK_MS
                    if ok:
                        print("⚡ Timing-based flick")

            # Execute scheduled flick if due
            # Scheduled flick path no longer used in toggle-on-2/off-4 mode
            scheduled_flick_ms = None

            # Light frame pacing; avoid heavy CPU
            time.sleep(0.04)

    finally:
        listener.stop()
        print("👋 Exiting attack flicker")


if __name__ == "__main__":
    main()


