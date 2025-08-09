#!/usr/bin/env python3
"""
Live crab detection test (color-based, cyan label)

Hotkeys:
- q: quit
- d: toggle debug
- -/=: decrease/increase min area (±1000)
- [/]: decrease/increase max area (±5000)
- ,/.: shift lower H (±2)
- </>: shift upper H (±2)
- s: print current HSV and area settings
"""

import os
import sys
import time
from typing import Optional, Tuple

import cv2
import numpy as np
from pynput import keyboard

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from color_detection import capture_screen, CRAB_COLOR


DEBUG = True
RUNNING = True

# HSV bounds (mutable copies)
lower_h, upper_h = [arr.copy() for arr in CRAB_COLOR['hsv_range']]

min_area_crab = 2000.0
max_area_crab = 120000.0
edge_margin = 2


def find_largest_region(mask) -> Optional[Tuple[Tuple[int, int], float, Tuple[int, int, int, int]]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    cx, cy = x + w // 2, y + h // 2
    area = float(cv2.contourArea(c))
    return (cx, cy), area, (x, y, w, h)


def is_valid_region(frame_shape, region, min_area: float, max_area: float, margin: int) -> bool:
    if region is None:
        return False
    area = float(region[1])
    x, y, w, h = region[2]
    h_img, w_img = frame_shape[:2]
    if area < min_area or area > max_area:
        return False
    if x <= margin or y <= margin or (x + w) >= (w_img - margin) or (y + h) >= (h_img - margin):
        return False
    return True


def on_key_press(key):
    global RUNNING, DEBUG, min_area_crab, max_area_crab, lower_h, upper_h
    try:
        ch = key.char
    except AttributeError:
        return
    if ch == 'q':
        RUNNING = False
        return False
    if ch == 'd':
        DEBUG = not DEBUG
        print(f"DEBUG {'ON' if DEBUG else 'OFF'}")
        return
    if ch == '-':
        min_area_crab = max(0.0, min_area_crab - 1000.0)
    elif ch == '=':
        min_area_crab += 1000.0
    elif ch == '[':
        max_area_crab = max(min_area_crab + 1000.0, max_area_crab - 5000.0)
    elif ch == ']':
        max_area_crab += 5000.0
    elif ch == ',':
        lower_h[0] = max(0, int(lower_h[0]) - 2)
    elif ch == '.':
        lower_h[0] = min(179, int(lower_h[0]) + 2)
    elif ch == '<':
        upper_h[0] = max(0, int(upper_h[0]) - 2)
    elif ch == '>':
        upper_h[0] = min(179, int(upper_h[0]) + 2)
    elif ch == 's':
        print_settings()
    if ch in '-=[],.<>':
        print_settings()


def print_settings():
    print(f"HSV lower={tuple(int(v) for v in lower_h)} upper={tuple(int(v) for v in upper_h)} | area_min={min_area_crab:.0f} area_max={max_area_crab:.0f}")


def main():
    global RUNNING
    print("🦀 Crab color detection test — press 'q' to quit, 'd' debug, 's' print settings")
    print_settings()
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    last_print = 0.0
    last_report = None
    try:
        while RUNNING:
            frame = capture_screen()
            if frame is None:
                time.sleep(0.05)
                continue
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower_h, upper_h)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
            region = find_largest_region(mask)
            valid = is_valid_region(frame.shape, region, min_area_crab, max_area_crab, edge_margin)

            now = time.time()
            if region is not None:
                (cx, cy), area, (x, y, w, h) = region
                report = (int(cx), int(cy), int(area), (x, y, w, h), valid)
            else:
                report = None

            if DEBUG and (report != last_report or (now - last_print) > 0.75):
                last_print = now
                if report is None:
                    print("Crab: none")
                else:
                    cx, cy, area_i, bbox, is_valid = report
                    print(f"Crab: pos=({cx},{cy}) area={area_i} bbox={bbox} valid={'YES' if is_valid else 'no'}")
                last_report = report
            time.sleep(0.06)
    finally:
        listener.stop()
        print("👋 Exiting crab detection test")


if __name__ == "__main__":
    main()


