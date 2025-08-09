#!/usr/bin/env python3
"""
Prayer Flick Test (number-detector driven)

Uses the template-based number detector to drive Quick-prayer toggles.
- Toggle ON on transition 2→1
- Toggle OFF on transition 1→4

Hotkeys:
  p = pause/resume
  q = quit
  d = toggle debug
  + / - = adjust min cooldown between toggles (ms)

Run:
  python auto_actions/ticks/pray_flick_test.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

import cv2
import numpy as np

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)
sys.path.append(CURRENT_DIR)

from funcs import AutoActionFunctions
from tm_detect import load_digit_templates, detect_digit_from_frame, load_all_templates, classify_digit_from_frame
from pynput import keyboard


PAUSED = True
STOP = False
DEBUG = False
MIN_COOLDOWN_MS = 160
MIN_CONF = 0.55
USE_STATE_CHECK = False  # set True to also verify orb state via template (slower)


def on_key(k):
    global PAUSED, STOP, DEBUG, MIN_COOLDOWN_MS
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
        elif k.char == '+':
            MIN_COOLDOWN_MS += 20
            print(f"Cooldown = {MIN_COOLDOWN_MS} ms")
        elif k.char == '-':
            MIN_COOLDOWN_MS = max(80, MIN_COOLDOWN_MS - 20)
            print(f"Cooldown = {MIN_COOLDOWN_MS} ms")
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
    print("Prayer Flick Test (ON at 2→1, OFF at 1→4)")
    print("Hotkeys: p=pause, q=quit, d=debug, +/- cooldown")
    print("⏸️  PAUSED - press 'p' to start")

    funcs = AutoActionFunctions()
    tdir = os.path.join(CURRENT_DIR, 'templates')
    all_templates = load_all_templates(tdir)
    print("Templates loaded:", {d: len(v) for d, v in all_templates.items()})
    if not any(all_templates.values()):
        print("❌ No templates found; create ticks/templates/2*.png and 4*.png")
        return

    listener = keyboard.Listener(on_press=on_key)
    listener.start()

    last_auto_ms = 0.0
    state_on = False  # tracked if USE_STATE_CHECK; otherwise inferred by transitions
    seq_last: Optional[int] = None
    expected_next: Optional[int] = None
    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue
            frame = funcs.capture_screen()
            if frame is None:
                time.sleep(0.03)
                continue
            now = time.time() * 1000.0
            # Optional state check (may be slower). Off by default per user request
            if USE_STATE_CHECK:
                try:
                    cur_on = funcs.is_quick_prayer_on(frame)
                    state_on = cur_on
                except Exception:
                    pass

            # Classify digit among all; require sufficient confidence and follow expected-next
            digit, score = classify_digit_from_frame(frame, all_templates, scales=(0.7,0.85,1.0,1.15))
            if DEBUG:
                print(f"digit={digit} score={score:.2f} state_on={state_on}")

            accepted = False
            def advance_from(d: int) -> int:
                return 4 if d == 1 else (d - 1)

            if digit is not None and score >= MIN_CONF and digit != seq_last:
                if seq_last is None or expected_next is None or digit == expected_next:
                    accepted = True
                    prev = seq_last
                    seq_last = digit
                    expected_next = advance_from(digit)
                    # Always log the digit sequence as requested
                    print(digit)

                    # Apply transition rules (this orientation): 2->1 ON, 1->4 OFF
                    if prev == 2 and digit == 1 and (now - last_auto_ms) >= MIN_COOLDOWN_MS:
                        if (not USE_STATE_CHECK) or (USE_STATE_CHECK and not state_on):
                            ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=50, settle_ms_max=90, hold_ms_min=50, hold_ms_max=85)
                            if ok:
                                print("⚡ Toggle ON (2->1)")
                                if USE_STATE_CHECK:
                                    state_on = True
                                last_auto_ms = now
                    elif prev == 1 and digit == 4 and (now - last_auto_ms) >= MIN_COOLDOWN_MS:
                        if (not USE_STATE_CHECK) or (USE_STATE_CHECK and state_on):
                            ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=50, settle_ms_max=90, hold_ms_min=50, hold_ms_max=85)
                            if ok:
                                print("⚡ Toggle OFF (1->4)")
                                if USE_STATE_CHECK:
                                    state_on = False
                                last_auto_ms = now
            time.sleep(0.02)
    finally:
        listener.stop()
        print("👋 Exiting flick test")


if __name__ == '__main__':
    main()


