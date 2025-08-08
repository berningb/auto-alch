#!/usr/bin/env python3
"""
Quick-Prayer Orb Calibration Tool

Hotkeys:
- 1: Save center at current mouse position
- 2: Save edge at current mouse position (computes radius)
- t: Test prayer flick once (mouse-based)
- s: Show current calibration
- q: Quit

Usage:
  python watchers/auto_actions/qp_calibrate.py

This writes to watchers/auto_actions/config.json using functions in funcs.py.
"""

import os
import sys
import time

# Ensure we can import funcs.py from this directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_DIR)

try:
    import pyautogui
    from pynput import keyboard
    from funcs import AutoActionFunctions
except Exception as e:
    print(f"❌ Missing dependency or import error: {e}")
    print("Install with: pip install pyautogui pynput")
    sys.exit(1)


def main():
    print("🔧 Quick-Prayer Calibration")
    print("=" * 40)
    print("- Move your mouse over the quick-prayer orb center, press '1'")
    print("- Move your mouse to any point on the orb edge, press '2'")
    print("- Press 't' to test a mouse-based pray flick")
    print("- Press 's' to show current calibration")
    print("- Press 'q' to quit")
    print()

    funcs = AutoActionFunctions()

    def on_press(key):
        try:
            if key.char == '1':
                x, y = pyautogui.position()
                funcs.set_quick_prayer_center(x, y)
            elif key.char == '2':
                x, y = pyautogui.position()
                funcs.set_quick_prayer_edge(x, y)
            elif key.char == 't':
                print("⏱️ Testing pray flick in 1s... move mouse away from orb if needed")
                time.sleep(1)
                ok = funcs.pray_tick(use_mouse=True)
                print("✅ Flick success" if ok else "❌ Flick failed")
            elif key.char == 's':
                print(f"📍 Center: {funcs.qp_center}  |  Radius: {funcs.qp_radius}")
            elif key.char == 'q':
                print("👋 Exiting calibration")
                return False
        except AttributeError:
            # Non-char keys ignored
            pass
        except Exception as e:
            print(f"⚠️ Error: {e}")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        while listener.is_alive():
            time.sleep(0.1)
    finally:
        listener.stop()


if __name__ == "__main__":
    main()


