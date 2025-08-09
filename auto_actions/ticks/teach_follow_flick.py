#!/usr/bin/env python3
"""
Teach-and-Follow Prayer Flicker

Goal: Mimic your exact clicks tied to the orange digit shown.

How it works
- Teach mode (default): You manually toggle Quick-prayer as you normally would.
  The script listens for your mouse clicks and records which digit (1..4)
  was on-screen at that exact moment. It alternates click parity to infer
  ON vs OFF (you can set the initial state). After enough samples, it derives
  the most common ON and OFF digits you use.

- Follow mode: It watches the digits and toggles automatically at your learned
  ON digit and OFF digit, with a short debounce to avoid double toggles.

Hotkeys
  p: pause/resume detection
  q: quit
  t: force Teach mode
  f: force Follow mode (after at least 4 samples per action)
  o: set current state = OFF (default)
  n: set current state = ON
  r: reset learned samples

Run:
  python auto_actions/ticks/teach_follow_flick.py
"""

from __future__ import annotations

import os
import sys
import time
from collections import Counter
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)
sys.path.append(CURRENT_DIR)

from funcs import AutoActionFunctions
from tm_detect import load_all_templates, classify_digit_from_frame
from pynput import keyboard, mouse


PAUSED = True
STOP = False


def main():
    print("Teach-and-Follow Flicker")
    print("Hotkeys: p=pause, q=quit, t=teach, f=follow, o=state OFF, n=state ON, r=reset")
    print("⏸️  PAUSED - press 'p' to start. Begin in TEACH mode; click as you normally do.")

    funcs = AutoActionFunctions()

    # Load digit templates 1..4
    templates = load_all_templates(os.path.join(CURRENT_DIR, 'templates'))
    if not any(templates.values()):
        print("❌ No digit templates found in ticks/templates")
        return

    # Teach state
    teach_mode = True
    follow_mode = False
    # Track current prayer state to split your clicks into ON vs OFF
    # Assume OFF initially (press 'o'/'n' to correct)
    is_on = False
    # Sample buckets
    on_samples: List[int] = []  # digits at which you toggle ON
    off_samples: List[int] = []  # digits at which you toggle OFF
    # Learned mapping
    learned_on_digit: Optional[int] = None
    learned_off_digit: Optional[int] = None
    # Detection cache
    last_digit: Optional[int] = None
    last_change_ms: Optional[float] = None
    # Debounce between auto-toggles
    last_auto_toggle_ms: float = 0.0
    min_cooldown_ms = 180.0

    # Click listener - record digit at your click time
    def on_click(x, y, button, pressed):
        nonlocal is_on, teach_mode, follow_mode, learned_on_digit, learned_off_digit
        if not pressed:
            return
        # Only learn in teach mode
        if not teach_mode:
            return
        d = last_digit
        if d is None:
            print("📝 Ignored click (no digit)")
            return
        if not is_on:
            on_samples.append(d)
            is_on = True
            print(f"📝 Teach: ON @ digit {d} (n_on={len(on_samples)})")
        else:
            off_samples.append(d)
            is_on = False
            print(f"📝 Teach: OFF @ digit {d} (n_off={len(off_samples)})")
        # Update learned digits when we have enough data
        if len(on_samples) >= 3:
            learned_on_digit = Counter(on_samples).most_common(1)[0][0]
        if len(off_samples) >= 3:
            learned_off_digit = Counter(off_samples).most_common(1)[0][0]
        if learned_on_digit and learned_off_digit and not follow_mode:
            print(f"✅ Learned mapping: ON@{learned_on_digit} OFF@{learned_off_digit}. Press 'f' to start following.")

    mlistener = mouse.Listener(on_click=on_click)
    mlistener.start()

    def on_key(k):
        nonlocal teach_mode, follow_mode, is_on, on_samples, off_samples, learned_on_digit, learned_off_digit
        global PAUSED, STOP
        try:
            if k.char == 'p':
                PAUSED = not PAUSED
                print("▶️ RUNNING" if not PAUSED else "⏸️  PAUSED")
            elif k.char == 'q':
                STOP = True
                return False
            elif k.char == 't':
                teach_mode = True
                follow_mode = False
                print("🧠 Teach mode")
            elif k.char == 'f':
                if learned_on_digit and learned_off_digit:
                    follow_mode = True
                    teach_mode = False
                    print(f"🤖 Follow mode: ON@{learned_on_digit} OFF@{learned_off_digit}")
                else:
                    print("⚠️ Need at least 3 samples for ON and OFF before following")
            elif k.char == 'o':
                is_on = False
                print("🔁 State set: OFF")
            elif k.char == 'n':
                is_on = True
                print("🔁 State set: ON")
            elif k.char == 'r':
                on_samples.clear(); off_samples.clear()
                learned_on_digit = None; learned_off_digit = None
                teach_mode = True; follow_mode = False
                print("🔄 Reset samples; back to Teach mode")
        except AttributeError:
            pass

    klistener = keyboard.Listener(on_press=on_key)
    klistener.start()

    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue

            frame = funcs.capture_screen()
            if frame is None:
                time.sleep(0.03)
                continue

            # Classify current digit (if any)
            d, score = classify_digit_from_frame(frame, templates, scales=(0.7, 0.85, 1.0, 1.15))
            now = time.time() * 1000.0
            if d != last_digit:
                last_digit = d
                last_change_ms = now

            # Follow mode: toggle exactly when learned digit appears
            if follow_mode and d is not None:
                if now - last_auto_toggle_ms >= min_cooldown_ms:
                    should_toggle = False
                    if not is_on and learned_on_digit is not None and d == learned_on_digit:
                        should_toggle = True
                        is_on = True
                        print(f"⚡ Auto ON @{d}")
                    elif is_on and learned_off_digit is not None and d == learned_off_digit:
                        should_toggle = True
                        is_on = False
                        print(f"⚡ Auto OFF @{d}")
                    if should_toggle:
                        ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=50, settle_ms_max=90, hold_ms_min=50, hold_ms_max=85)
                        if ok:
                            last_auto_toggle_ms = now

            time.sleep(0.02)
    finally:
        mlistener.stop()
        klistener.stop()
        print("👋 Exiting teach-and-follow")


if __name__ == '__main__':
    main()


