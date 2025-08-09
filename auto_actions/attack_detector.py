#!/usr/bin/env python3
"""
Attack Detector

Detects orange damage numbers on screen and logs them.
This is designed to detect combat damage numbers in RuneScape.

Features:
- Detects orange damage numbers using color filtering
- Uses OCR to read the exact damage values
- Logs all detected damage with timestamps
- Real-time monitoring with hotkey controls

Hotkeys:
- p: pause / resume
- q: quit
- d: toggle debug mode
- c: set custom detection region around mouse
- x: clear custom region

Requirements:
- Uses HSV color detection to isolate orange damage text
- Uses pytesseract for OCR of damage numbers
- Saves detected damage to log file

Run:
  python auto_actions/attack_detector.py
"""

from __future__ import annotations

import os
import sys
import time
import json
from typing import Optional, Tuple, List
from datetime import datetime

import cv2
import numpy as np
import pyautogui

# Add auto_actions to path for AutoActionFunctions
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
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
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Try to import OCR for damage number detection
try:
    import pytesseract
    HAS_TESS = True
    print("✅ OCR available for damage number detection")
except ImportError:
    HAS_TESS = False
    print("⚠️ OCR not available - install pytesseract for damage number detection")


# HSV ranges for RuneScape orange damage numbers
# These ranges target the specific orange color used for damage text
HSV_ORANGE_DAMAGE_RANGES = [
    # Primary orange range for damage numbers (targeting RGB ~255,125,0)
    (np.array([20, 200, 200]), np.array([35, 255, 255])),
    # Secondary range for variations due to anti-aliasing/smoothing
    (np.array([15, 150, 150]), np.array([40, 255, 255])),
    # Wider range for different monitor/graphics settings
    (np.array([10, 100, 100]), np.array([45, 255, 255])),
]

# Global state
PAUSED = True
STOP = False
DEBUG = True
CUSTOM_ROI = None  # (x1, y1, x2, y2) if user sets a manual region
DAMAGE_LOG = []  # Store detected damage numbers with timestamps
LOG_FILE = os.path.join(CURRENT_DIR, "data", "damage_log.json")

# Ensure data directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def on_key_press(key):
    """Handle keyboard inputs for control"""
    global PAUSED, STOP, DEBUG, CUSTOM_ROI
    try:
        if key.char == 'p':
            PAUSED = not PAUSED
            print("▶️  RUNNING" if not PAUSED else "⏸️  PAUSED")
        elif key.char == 'q':
            STOP = True
            print("🛑 QUIT requested")
            return False
        elif key.char == 'd':
            DEBUG = not DEBUG
            print(f"🐛 Debug mode: {'ON' if DEBUG else 'OFF'}")
        elif key.char == 'c':
            # Set ROI - user should position mouse near where damage numbers appear
            x, y = pyautogui.position()
            margin = 100  # Larger margin for damage detection
            CUSTOM_ROI = (x - margin, y - margin, x + margin, y + margin)
            print(f"📍 Set detection ROI: {CUSTOM_ROI} (around mouse position)")
        elif key.char == 'x':
            CUSTOM_ROI = None
            print("🗑️ Cleared ROI - will scan full screen")
    except AttributeError:
        pass


def save_damage_log():
    """Save the damage log to file"""
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump(DAMAGE_LOG, f, indent=2)
        print(f"💾 Saved {len(DAMAGE_LOG)} damage entries to {LOG_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to save damage log: {e}")


def log_damage(damage_value: int, position: Tuple[int, int], confidence: float = 1.0):
    """Log a detected damage number"""
    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "damage": damage_value,
        "position": position,
        "confidence": confidence
    }
    DAMAGE_LOG.append(entry)
    
    # Display the damage
    time_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{time_str}] 💥 Damage: {damage_value} at {position} (conf: {confidence:.2f})")
    
    # Auto-save every 10 entries
    if len(DAMAGE_LOG) % 10 == 0:
        save_damage_log()


def detect_orange_damage_numbers(frame) -> List[Tuple[int, Tuple[int, int], float]]:
    """
    Detect orange damage numbers on screen
    
    Returns:
        List of tuples: (damage_value, position, confidence)
    """
    try:
        # Get ROI
        if CUSTOM_ROI:
            x1, y1, x2, y2 = CUSTOM_ROI
            x1, y1, x2, y2 = max(0, x1), max(0, y1), min(frame.shape[1], x2), min(frame.shape[0], y2)
            roi = frame[y1:y2, x1:x2]
            roi_offset = (x1, y1)
            if DEBUG:
                print(f"🔍 Using custom ROI: {CUSTOM_ROI}")
        else:
            # Use full screen for damage detection
            roi = frame
            roi_offset = (0, 0)
            if DEBUG:
                print("🔍 Scanning full screen for damage numbers")
        
        if roi.size == 0:
            if DEBUG:
                print("⚠️ ROI is empty")
            return []
            
        # Convert to HSV for orange detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Debug: Show HSV range in ROI
        if DEBUG:
            h_min, h_max = hsv[:,:,0].min(), hsv[:,:,0].max()
            s_min, s_max = hsv[:,:,1].min(), hsv[:,:,1].max() 
            v_min, v_max = hsv[:,:,2].min(), hsv[:,:,2].max()
            print(f"🎨 HSV ranges in ROI - H:[{h_min}-{h_max}] S:[{s_min}-{s_max}] V:[{v_min}-{v_max}]")
        
        # Create mask for orange damage colors
        orange_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        for lower, upper in HSV_ORANGE_DAMAGE_RANGES:
            mask_range = cv2.inRange(hsv, lower, upper)
            orange_mask = cv2.bitwise_or(orange_mask, mask_range)
        
        # Count orange pixels for debugging
        orange_pixels = cv2.countNonZero(orange_mask)
        if DEBUG:
            print(f"🟠 Found {orange_pixels} orange pixels")
        
        if orange_pixels < 10:  # Not enough orange detected
            return []
        
        # Find contours for number-like shapes
        contours, _ = cv2.findContours(orange_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if DEBUG:
            print(f"🔍 Found {len(contours)} contours")
        
        detected_numbers = []
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if DEBUG:
                print(f"  Contour {i}: area={area}")
            
            # Filter by size - damage numbers are typically small to medium sized
            if 20 < area < 5000:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                if DEBUG:
                    print(f"  Contour {i}: bbox=({x},{y},{w},{h}), aspect={aspect_ratio:.2f}")
                
                # Filter by aspect ratio - numbers are typically taller than they are wide
                if 0.3 < aspect_ratio < 5.0:
                    # Extract the region containing the potential number
                    number_roi = orange_mask[y:y+h, x:x+w]
                    
                    # Scale up for better OCR if the region is small
                    scale_factor = max(2, 60 // max(w, h))
                    if scale_factor > 1:
                        number_roi = cv2.resize(number_roi, None, fx=scale_factor, fy=scale_factor, 
                                              interpolation=cv2.INTER_NEAREST)
                    
                    if HAS_TESS:
                        # OCR configuration for damage numbers (digits only, no letters)
                        config = '--psm 8 -c tessedit_char_whitelist=0123456789'
                        try:
                            text = pytesseract.image_to_string(number_roi, config=config).strip()
                            if DEBUG:
                                print(f"  OCR result: '{text}'")
                            
                            # Validate that we got a valid damage number
                            if text.isdigit() and len(text) >= 1:
                                damage_value = int(text)
                                if 0 <= damage_value <= 99999:  # Reasonable damage range
                                    # Calculate absolute position on screen
                                    abs_x = roi_offset[0] + x + w // 2
                                    abs_y = roi_offset[1] + y + h // 2
                                    position = (abs_x, abs_y)
                                    
                                    # Calculate confidence based on OCR clarity and area
                                    confidence = min(1.0, area / 1000.0)  # Simple confidence metric
                                    
                                    detected_numbers.append((damage_value, position, confidence))
                                    
                                    if DEBUG:
                                        print(f"  ✅ Valid damage number: {damage_value} at {position}")
                        except Exception as ocr_err:
                            if DEBUG:
                                print(f"  OCR error: {ocr_err}")
                    else:
                        # Fallback without OCR - just detect that there's an orange number-like shape
                        if DEBUG:
                            print("  No OCR available, detected orange number-like shape")
                        # We could implement template matching here for common damage numbers
                        
        return detected_numbers
        
    except Exception as e:
        if DEBUG:
            print(f"⚠️ Detection error: {e}")
        return []


def main():
    """Main detection loop"""
    print("🎯 Attack Damage Detector")
    print("=" * 50)
    print("Hotkeys:")
    print("  p = pause/resume detection")
    print("  q = quit")
    print("  d = toggle debug output")
    print("  c = set detection region around mouse cursor")
    print("  x = clear custom detection region")
    print("=" * 50)
    print("⏸️  PAUSED - Press 'p' to start detection")

    funcs = AutoActionFunctions()
    
    # Set up keyboard listener
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    # Detection state
    last_detections = []
    detection_cooldown = {}  # Prevent spam of same damage numbers
    
    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue

            now = time.time()

            if DEBUG:
                print("📸 Capturing screen for damage detection...")
            
            # Capture screen
            frame = funcs.capture_screen()
            if frame is not None:
                if DEBUG:
                    print(f"📸 Screen captured: {frame.shape}")
                
                # Detect damage numbers
                detected_numbers = detect_orange_damage_numbers(frame)
                
                # Process each detected number
                for damage_value, position, confidence in detected_numbers:
                    # Create a unique key for this detection (position-based to avoid duplicates)
                    detection_key = f"{damage_value}_{position[0]//20}_{position[1]//20}"
                    
                    # Check cooldown to prevent spam (same damage in nearby position)
                    if detection_key not in detection_cooldown or (now - detection_cooldown[detection_key]) > 2.0:
                        log_damage(damage_value, position, confidence)
                        detection_cooldown[detection_key] = now
                    elif DEBUG:
                        print(f"  🔄 Skipped duplicate: {damage_value} (cooldown)")
            
            # Light frame pacing to avoid heavy CPU usage
            time.sleep(0.1)  # Check every 100ms

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    finally:
        listener.stop()
        save_damage_log()
        print("👋 Exiting attack damage detector")
        print(f"📊 Total damage entries logged: {len(DAMAGE_LOG)}")


if __name__ == "__main__":
    main()

