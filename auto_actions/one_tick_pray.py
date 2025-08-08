#!/usr/bin/env python3
"""
One-Tick Prayer Flicker

Hotkeys:
- p: toggle pause/resume
- q: quit
- = / - : increase/decrease target tick by 1 ms
- ] / [ : increase/decrease settle time by 5 ms

Default timings target ~1 tick (~600–620 ms) on typical servers.
Requires quick-prayer orb calibration (run qp_calibrate.py).
"""

import os
import sys
import time
import random

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

try:
    from pynput import keyboard
    from funcs import AutoActionFunctions
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


PAUSED = True
STOP = False


def on_key_press(key):
    global PAUSED, STOP, tick_ms, settle_min, settle_max
    try:
        if key.char == 'p':
            PAUSED = not PAUSED
            print("▶️  RUNNING" if not PAUSED else "⏸️  PAUSED")
        elif key.char == 'q':
            STOP = True
            print("🛑 QUIT requested")
            return False
        elif key.char == '=':
            tick_ms = min(800, tick_ms + 1)
            print(f"⏱️ tick_ms={tick_ms}")
        elif key.char == '-':
            tick_ms = max(560, tick_ms - 1)
            print(f"⏱️ tick_ms={tick_ms}")
        elif key.char == ']':
            settle_min = min(180, settle_min + 5)
            settle_max = min(200, max(settle_min, settle_max + 5))
            print(f"🧘 settle={settle_min}-{settle_max}ms")
        elif key.char == '[':
            settle_min = max(20, settle_min - 5)
            settle_max = max(settle_min, settle_max - 5)
            print(f"🧘 settle={settle_min}-{settle_max}ms")
    except AttributeError:
        pass


def main():
    global tick_ms, settle_min, settle_max
    print("✝️  One-Tick Prayer Flicker")
    print("Hotkeys: p=pause/resume, q=quit, +/- tick ms, [/]=settle ms")
    print("⏸️  PAUSED - Press 'p' to start")

    funcs = AutoActionFunctions()
    if not funcs.qp_center:
        print("⚠️ No quick-prayer calibration found. Run qp_calibrate.py first for best reliability.")

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    # Default timings tuned to ~616 ms servers
    tick_ms = 616
    settle_min, settle_max = 80, 120

    try:
        while not STOP:
            if PAUSED:
                time.sleep(0.05)
                continue

            start = time.time()

            # Tick-aware flick with randomized in-orb points and held left-clicks
            funcs.pray_tick(
                use_mouse=True,
                min_gap_ms=70,
                max_gap_ms=100,
                settle_ms_min=settle_min,
                settle_ms_max=settle_max,
                hold_on_ms_min=70,
                hold_on_ms_max=100,
                hold_off_ms_min=70,
                hold_off_ms_max=100,
            )

            elapsed_ms = (time.time() - start) * 1000.0
            # Sleep to complete one tick; add light jitter to avoid robotic cadence
            target_sleep = max(0.0, (tick_ms - elapsed_ms) / 1000.0)
            jitter = random.uniform(-0.012, 0.012)
            time.sleep(max(0.0, target_sleep + jitter))

    finally:
        listener.stop()
        print("👋 Exiting flicker")


if __name__ == "__main__":
    main()


