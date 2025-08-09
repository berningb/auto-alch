#!/usr/bin/env python3
"""
Log tick index 1 2 3 4 based on first occurrence of each tick change.

We use the template-based number classifier to detect when the orange digit
changes. On each change, we advance an index (1..4) and print it once. This
avoids spam like 4 4 4 4 and instead produces 1 2 3 4 1 2 3 4 ...

Hotkeys: p=pause/resume, q=quit, d=debug

Run:
  python auto_actions/ticks/log_tick_index.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

import cv2
import numpy as np
from pynput import keyboard

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)
sys.path.append(CURRENT_DIR)

from funcs import AutoActionFunctions
from tm_detect import load_all_templates, classify_digit_from_frame


PAUSED = True
STOP = False
DEBUG = False
MIN_CONF = 0.55


def on_key(k):
    global PAUSED, STOP, DEBUG
    try:
        if k.char == 'p':
            PAUSED = not PAUSED
            print("▶️ RUNNING" if not PAUSED else "⏸️ PAUSED")
        elif k.char == 'q':
            STOP = True
            return False
        elif k.char == 'd':
            DEBUG = not DEBUG
            print(f"DEBUG {'ON' if DEBUG else 'OFF'}")
        elif k.char == '=':
            global MIN_CONF
            MIN_CONF = min(0.9, MIN_CONF + 0.05)
            print(f"Confidence >= {MIN_CONF:.2f}")
        elif k.char == '_':
            MIN_CONF = max(0.35, MIN_CONF - 0.05)
            print(f"Confidence >= {MIN_CONF:.2f}")
    except AttributeError:
        pass


def main():
    print("Tick index logger (prints 1 2 3 4 on each new tick)")
    print("Hotkeys: p=pause, q=quit, d=debug")
    print("⏸️  PAUSED - press 'p' to start")

    funcs = AutoActionFunctions()
    tdir = os.path.join(CURRENT_DIR, 'templates')
    all_templates = load_all_templates(tdir)
    if not any(all_templates.values()):
        print("❌ No templates found in ticks/templates")
        return

    listener = keyboard.Listener(on_press=on_key)
    listener.start()

    last_digit: Optional[int] = None
    last_output: Optional[int] = None
    expected_next: Optional[int] = None
    last_output_ms: Optional[float] = None
    tick_ms_est = 616.0

    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue
            frame = funcs.capture_screen()
            if frame is None:
                time.sleep(0.03)
                continue
            digit, score = classify_digit_from_frame(frame, all_templates, scales=(0.7, 0.85, 1.0, 1.15))
            if DEBUG:
                print(f"digit={digit} score={score:.2f}")
            now = time.time() * 1000.0

            def advance_from(d: int):
                nonlocal expected_next
                return 4 if d == 1 else (d - 1)

            # Candidate acceptance logic
            accepted = False
            if digit is not None and digit != last_digit and score >= MIN_CONF:
                # If no prior output, seed sequence with the observed digit
                if last_output is None:
                    print(digit)
                    last_output = digit
                    expected_next = advance_from(digit)
                    last_output_ms = now
                    accepted = True
                else:
                    # Accept only if it matches the expected next, with a small minimum interval
                    min_interval = tick_ms_est * 0.4
                    if now - (last_output_ms or 0) >= min_interval and (
                        digit == expected_next or (now - (last_output_ms or 0)) >= tick_ms_est * 1.5
                    ):
                        # Update tick estimate on acceptance
                        dt = now - (last_output_ms or now)
                        if 300.0 <= dt <= 900.0:
                            tick_ms_est = (tick_ms_est * 0.7) + (dt * 0.3)
                        print(digit)
                        last_output = digit
                        expected_next = advance_from(digit)
                        last_output_ms = now
                        accepted = True
                last_digit = digit

            # Fallback: infer next in sequence based on timing if we didn't accept detection
            if not accepted and last_output is not None and last_output_ms is not None:
                if now - last_output_ms >= tick_ms_est * 0.95:
                    inferred = expected_next or advance_from(last_output)
                    print(inferred)
                    last_output = inferred
                    expected_next = advance_from(inferred)
                    last_output_ms = now
            time.sleep(0.02)
    finally:
        listener.stop()
        print("👋 Exiting tick index logger")


if __name__ == '__main__':
    main()


