#!/usr/bin/env python3
"""
Watch and Click - Reactive color-based clicker
Watches the screen continuously and clicks once on whichever is available:
- Cyan crab label
- Magenta tunnel label

Hotkeys:
- p: toggle pause/resume
- s: pause
- q: quit
- d: toggle debug (prints detection info)
"""

import sys
import os
import time
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyautogui
from pynput import keyboard
from color_detection import capture_screen, TUNNEL_COLOR, CRAB_COLOR
import cv2
import numpy as np

# Pull HSV ranges from color_detection definitions to keep in sync
CYAN_RANGE = CRAB_COLOR['hsv_range']       # crab
MAGENTA_RANGE = TUNNEL_COLOR['hsv_range']  # tunnel

PAUSED = True
STOP = False
DEBUG = False


def on_key_press(key):
    global PAUSED, STOP, DEBUG
    try:
        if key.char == 'p':
            PAUSED = not PAUSED
            print("▶️  UNPAUSED (watching...)" if not PAUSED else "⏸️  PAUSED")
        elif key.char == 's':
            PAUSED = True
            print("⏸️  PAUSED")
        elif key.char == 'q':
            STOP = True
            print("🛑 QUIT requested")
            return False
        elif key.char == 'd':
            DEBUG = not DEBUG
            print(f"🔎 DEBUG {'ON' if DEBUG else 'OFF'}")
    except AttributeError:
        pass


def wait_until_unpaused():
    global PAUSED, STOP
    while PAUSED and not STOP:
        time.sleep(0.05)


def find_largest_region(mask) -> Optional[Tuple[Tuple[int, int], float, Tuple[int, int, int, int]]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    cx, cy = x + w // 2, y + h // 2
    area = float(cv2.contourArea(c))
    return (cx, cy), area, (x, y, w, h)


def detect_color(hsv, range_tuple):
    lower_hsv, upper_hsv = range_tuple
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
    return find_largest_region(mask)


def click_at(point: Tuple[int, int]):
    x, y = point
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.02)
    pyautogui.click()


def main():
    global PAUSED, STOP, DEBUG
    print("👀 Watch and Click - Cyan crab or Magenta tunnel")
    print("Hotkeys: p=toggle pause, s=pause, q=quit, d=debug")
    print("Click happens once per appearance; when it disappears and reappears, it will click again.")
    print("⏸️  PAUSED - Press 'p' to start")

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    # One-click-per-appearance with debounce: click once, then require
    # a continuous absence period before re-arming another click
    crab_clicked = False
    tunnel_clicked = False
    crab_last_seen = 0.0
    tunnel_last_seen = 0.0
    rearm_absence_secs_crab = 0.8
    rearm_absence_secs_tunnel = 0.6

    # Minimum area to treat as a valid target (filter noise)
    min_area_crab = 2500.0
    min_area_tunnel = 1500.0

    last_debug_time = 0.0

    try:
        while not STOP:
            wait_until_unpaused()
            if STOP:
                break

            frame = capture_screen()
            if frame is None:
                time.sleep(0.05)
                continue

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            crab = detect_color(hsv, CYAN_RANGE)
            tunnel = detect_color(hsv, MAGENTA_RANGE)

            crab_visible = crab is not None and crab[1] >= min_area_crab
            tunnel_visible = tunnel is not None and tunnel[1] >= min_area_tunnel

            # Debug info every ~0.5s
            now = time.time()
            if DEBUG and now - last_debug_time > 0.5:
                crab_area = f"{crab[1]:.0f}" if crab else "0"
                tun_area = f"{tunnel[1]:.0f}" if tunnel else "0"
                print(f"🔎 crab_area={crab_area} (min {min_area_crab:.0f}), tunnel_area={tun_area} (min {min_area_tunnel:.0f})")
                last_debug_time = now

            # Debounced one-time click per continuous appearance
            now = time.time()

            # Update last-seen timestamps
            if crab_visible:
                crab_last_seen = now
                if not crab_clicked:
                    (cx, cy), area, _ = crab
                    print(f"🎯 Clicking crab at ({cx},{cy}) area={area:.0f}")
                    click_at((cx, cy))
                    crab_clicked = True
            else:
                # Rearm only after sustained absence
                if crab_clicked and (now - crab_last_seen) >= rearm_absence_secs_crab:
                    crab_clicked = False

            if tunnel_visible:
                tunnel_last_seen = now
                if not tunnel_clicked and not crab_visible:
                    # Prefer crab over tunnel when both present; only click tunnel
                    # if crab is not currently visible
                    (cx, cy), area, _ = tunnel
                    print(f"🎯 Clicking tunnel at ({cx},{cy}) area={area:.0f}")
                    click_at((cx, cy))
                    tunnel_clicked = True
            else:
                if tunnel_clicked and (now - tunnel_last_seen) >= rearm_absence_secs_tunnel:
                    tunnel_clicked = False

            time.sleep(0.05)

    finally:
        listener.stop()
        print("👋 Stopped watcher")


if __name__ == "__main__":
    main()
