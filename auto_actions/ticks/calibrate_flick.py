#!/usr/bin/env python3
"""
Calibration harness for prayer toggle timing.

What it does:
- Detects orange countdown via templates (focus on digit '2')
- Schedules a single Quick-prayer toggle at (detect_time + base_delay_ms)
- Lets you press '+' when you believe the toggle should occur (ideal time)
- Computes error = ideal_time - scheduled_time and aggregates stats
- Prints running mean/median and recommends a new base_delay

Hotkeys:
  p = pause/resume
  q = quit
  + = mark ideal toggle moment (compared to last schedule)
  [ / ] = decrease / increase base_delay by 10 ms
  r = reset stats

Run:
  python auto_actions/ticks/calibrate_flick.py
"""

from __future__ import annotations

import os
import sys
import time
import json
import statistics as stats
from typing import List, Optional, Tuple

import cv2
import numpy as np

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(ROOT_DIR)
sys.path.append(CURRENT_DIR)

# Import helpers
from funcs import AutoActionFunctions
from tm_detect import load_digit_templates, detect_digit_from_frame
from pynput import keyboard


PAUSED = True
STOP = False


def main():
    print("Prayer Toggle Timing Calibrator (teach by pressing '+')")
    print("Hotkeys: p=pause/resume, q=quit, +=mark ideal, [ / ] adjust base, r=reset stats")
    print("⏸️  PAUSED - Press 'p'. It will NOT toggle until you provide enough '+' samples.")

    funcs = AutoActionFunctions()

    # Templates
    templates_dir = os.path.join(CURRENT_DIR, 'templates')
    t2 = load_digit_templates(templates_dir, '2')
    t4 = load_digit_templates(templates_dir, '4')
    if not t2:
        print(f"❌ No '2' templates in {templates_dir}")
        return
    print(f"✅ Loaded {len(t2)} '2' templates; {len(t4)} '4' templates")

    # State
    base_delay_ms: float = 160.0  # starting guess for ON (2)
    base_delay_off_ms: float = 160.0  # starting guess for OFF (4)
    last_schedule_time: Optional[float] = None
    last_toggle_time: Optional[float] = None
    last_detect2_time: Optional[float] = None
    last_detect4_time: Optional[float] = None
    samples_ms: List[float] = []
    samples_off_ms: List[float] = []
    ACTIVE = False  # stays False until 5 ON and 5 OFF samples are provided

    # Persist learned delay across runs
    store_path = os.path.join(ROOT_DIR, 'data', 'flick_timing.json')
    try:
        if os.path.exists(store_path):
            with open(store_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            d = data.get('delay_ms')
            if isinstance(d, (int, float)):
                base_delay_ms = float(d)
                print(f"📦 Loaded prior learned delay: {int(base_delay_ms)} ms")
            doff = data.get('delay_off_ms')
            if isinstance(doff, (int, float)):
                base_delay_off_ms = float(doff)
                print(f"📦 Loaded prior learned off-delay: {int(base_delay_off_ms)} ms")
            if isinstance(data.get('samples'), list):
                for v in data['samples']:
                    try:
                        samples_ms.append(float(v))
                    except Exception:
                        pass
            if isinstance(data.get('samples_off'), list):
                for v in data['samples_off']:
                    try:
                        samples_off_ms.append(float(v))
                    except Exception:
                        pass
            # Auto-arm if we already have enough complete toggles
            if len(samples_ms) >= 5 and len(samples_off_ms) >= 5:
                ACTIVE = True
                print(f"✅ Auto-armed from saved data (ON={len(samples_ms)}, OFF={len(samples_off_ms)})")
            else:
                print(f"📦 Loaded ON={len(samples_ms)} OFF={len(samples_off_ms)}; will arm after 5/5 complete toggles")
    except Exception:
        pass

    def on_key(k):
        nonlocal base_delay_ms, base_delay_off_ms, last_schedule_time, samples_ms, samples_off_ms, ACTIVE, last_detect2_time, last_detect4_time
        global PAUSED, STOP
        try:
            if k.char == 'p':
                PAUSED = not PAUSED
                print("▶️ RUNNING" if not PAUSED else "⏸️  PAUSED")
            elif k.char == 'q':
                STOP = True
                return False
            elif k.char == '+':
                now = time.time() * 1000.0
                # Prefer most recent detection among 2/4
                target = None
                if last_detect2_time and (not last_detect4_time or last_detect2_time >= last_detect4_time):
                    target = '2'
                elif last_detect4_time:
                    target = '4'
                if target is None:
                    print("➕ mark ignored (no recent '2'/'4' detection)")
                elif target == '2':
                    cand = max(0.0, now - last_detect2_time)
                    samples_ms.append(cand)
                    med = stats.median(samples_ms)
                    base_delay_ms = med
                    print(f"➕ ON sample={int(cand)} ms  n={len(samples_ms)}  median={int(med)} ms")
                    # If active, immediately re-schedule using the new delay
                    if ACTIVE and last_detect2_time is not None:
                        last_schedule_time = last_detect2_time + base_delay_ms
                        print(f"🗓️  Re-schedule ON in {int(max(0.0, last_schedule_time - now))} ms")
                else:
                    cand = max(0.0, now - last_detect4_time)
                    samples_off_ms.append(cand)
                    med = stats.median(samples_off_ms)
                    base_delay_off_ms = med
                    print(f"➕ OFF sample={int(cand)} ms  n={len(samples_off_ms)}  median={int(med)} ms")
                    if ACTIVE and last_detect4_time is not None:
                        last_schedule_time = last_detect4_time + base_delay_off_ms
                        print(f"🗓️  Re-schedule OFF in {int(max(0.0, last_schedule_time - now))} ms")
                    # Save
                    try:
                        os.makedirs(os.path.join(ROOT_DIR, 'data'), exist_ok=True)
                        with open(store_path, 'w', encoding='utf-8') as f:
                            json.dump({'delay_ms': base_delay_ms,
                                       'delay_off_ms': base_delay_off_ms,
                                       'samples': samples_ms,
                                       'samples_off': samples_off_ms,
                                       'updated_at': int(time.time())}, f, indent=2)
                    except Exception:
                        pass
                    # Auto-arm once we have 5/5 complete toggles
                    if not ACTIVE and len(samples_ms) >= 5 and len(samples_off_ms) >= 5:
                        ACTIVE = True
                        print(f"✅ Enough samples collected — auto mode ENABLED (ON≈{int(base_delay_ms)} ms, OFF≈{int(base_delay_off_ms)} ms)")
            elif k.char == '[':
                base_delay_ms = max(0.0, base_delay_ms - 10.0)
                print(f"⏬ base_delay = {int(base_delay_ms)} ms")
            elif k.char == ']':
                base_delay_ms += 10.0
                print(f"⏫ base_delay = {int(base_delay_ms)} ms")
            elif k.char == 'r':
                samples_ms.clear()
                samples_off_ms.clear()
                ACTIVE = False
                print("🔄 stats reset")
        except AttributeError:
            pass

    listener = keyboard.Listener(on_press=on_key)
    listener.start()

    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue
            frame = funcs.capture_screen()
            if frame is None:
                time.sleep(0.03)
                continue
            # Detect 2 or 4; if active, schedule toggles based on learned delays
            if detect_digit_from_frame(frame, t2, threshold=0.50):
                now = time.time() * 1000.0
                last_detect2_time = now
                if ACTIVE:
                    if last_schedule_time is None or (now - (last_toggle_time or 0.0)) > 400:
                        last_schedule_time = now + base_delay_ms
                        print(f"🗓️ schedule ON @ +{int(base_delay_ms)} ms")
            elif t4 and detect_digit_from_frame(frame, t4, threshold=0.50):
                now = time.time() * 1000.0
                last_detect4_time = now
                if ACTIVE:
                    if last_schedule_time is None or (now - (last_toggle_time or 0.0)) > 400:
                        last_schedule_time = now + base_delay_off_ms
                        print(f"🗓️ schedule OFF @ +{int(base_delay_off_ms)} ms")
            # Execute if due
            now = time.time() * 1000.0
            if last_schedule_time is not None and now >= last_schedule_time:
                ok = funcs.quick_prayer_toggle(use_mouse=True, settle_ms_min=60, settle_ms_max=110, hold_ms_min=55, hold_ms_max=90)
                if ok:
                    print("⚡ toggle")
                last_toggle_time = now
                last_schedule_time = None
            time.sleep(0.02)
    finally:
        listener.stop()
        print("👋 Exiting calibrator")


if __name__ == '__main__':
    main()


