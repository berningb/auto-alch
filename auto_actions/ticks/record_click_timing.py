#!/usr/bin/env python3
"""
Record timing between detected orange digit changes and your mouse clicks.

Writes CSV to auto_actions/data/click_timing.csv with columns:
  timestamp_ms, digit, digit_conf, ms_since_last_digit_change, mouse_x, mouse_y

Run:
  python auto_actions/ticks/record_click_timing.py
Press Ctrl+C to stop.
"""

from __future__ import annotations

import csv
import os
import sys
import time
from typing import Optional

import cv2
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(ROOT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, 'click_timing.csv')

sys.path.append(BASE_DIR)
try:
    from mss import mss  # type: ignore
except Exception:
    mss = None

try:
    from pynput import mouse, keyboard
except Exception as e:
    print(f"❌ pynput required: {e}")
    sys.exit(1)

try:
    from tm_detect import load_all_templates, classify_digit_from_frame
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def capture_bgr():
    if mss is not None:
        grab = mss()
        mon = grab.monitors[1]
        def _cap():
            img = np.asarray(grab.grab(mon))
            return img[:, :, :3][:, :, ::-1]
        return _cap
    else:
        import pyautogui  # type: ignore
        def _cap():
            shot = pyautogui.screenshot()
            return cv2.cvtColor(np.array(shot), cv2.COLOR_RGB2BGR)
        return _cap


def main():
    # Pause gate
    print("⏸️  Paused - click into your game, then press 'p' to start recording. (q to quit)")
    is_paused = True
    should_stop = False

    def on_key(key):
        nonlocal is_paused, should_stop
        try:
            if key.char == 'p':
                is_paused = False
                print("▶️  Recording started")
                return False
            if key.char == 'q':
                should_stop = True
                return False
        except AttributeError:
            pass

    klistener = keyboard.Listener(on_press=on_key)
    klistener.start()
    while is_paused and not should_stop:
        time.sleep(0.05)
    klistener.stop()
    if should_stop:
        return

    templates_dir = os.path.join(BASE_DIR, 'templates')
    templates_by_digit = load_all_templates(templates_dir)
    if not any(templates_by_digit.values()):
        print(f"❌ No templates found under {templates_dir}")
        sys.exit(1)

    cap = capture_bgr()

    last_digit: Optional[int] = None
    last_digit_change_ms: Optional[float] = None
    current_digit: Optional[int] = None
    current_conf: float = -1.0
    cur_ms = lambda: time.time() * 1000.0

    # Mouse listener to log clicks
    def on_click(x, y, button, pressed):
        nonlocal current_digit, current_conf, last_digit_change_ms
        if pressed:
            ts = cur_ms()
            delta = ts - last_digit_change_ms if last_digit_change_ms is not None else -1.0
            with open(CSV_PATH, 'a', newline='') as f:
                w = csv.writer(f)
                w.writerow([int(ts), current_digit if current_digit is not None else '', f"{current_conf:.3f}", int(delta) if delta>=0 else '', x, y])
            print(f"🖱️ click: digit={current_digit} conf={current_conf:.2f} Δ={int(delta)}ms @({x},{y})")

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    # Header
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['timestamp_ms','digit','digit_conf','ms_since_last_digit_change','mouse_x','mouse_y'])
    print(f"📄 Logging to {CSV_PATH}")

    try:
        while True:
            frame = cap()
            d, score = classify_digit_from_frame(frame, templates_by_digit, scales=(0.7,0.85,1.0,1.15,1.3))
            current_digit, current_conf = d, (score if score is not None else -1.0)
            if d is not None and d != last_digit:
                last_digit = d
                last_digit_change_ms = cur_ms()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print("👋 Stopped timing recorder")


if __name__ == '__main__':
    main()


