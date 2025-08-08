#!/usr/bin/env python3
"""
Record human mouse movement while you click the quick-prayer orb.

What it does:
- Samples mouse position at high frequency (default 240 Hz) for a fixed duration (default 60s)
- Logs click down/up events with precise timestamps
- Saves raw events to data/mouse_profile_<timestamp>.jsonl
- Saves a summary JSON with simple distributions to data/mouse_profile_<timestamp>_summary.json

Hotkeys (while running):
- q: quit early

Usage:
  python watchers/auto_actions/record_mouse_profile.py

Tip: Run qp_calibrate.py beforehand so the script can compute relative-to-orb stats.
"""

import os
import sys
import json
import time
import math
import threading
from datetime import datetime

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

sys.path.append(CURRENT_DIR)

try:
    import pyautogui
    from pynput import mouse, keyboard
    from funcs import AutoActionFunctions
except Exception as e:
    print(f"❌ Missing dependency or import error: {e}")
    print("Install with: pip install pyautogui pynput")
    sys.exit(1)


def record(duration_s: float = 60.0, sample_hz: float = 240.0):
    funcs = AutoActionFunctions()
    qp_center = funcs.qp_center  # may be None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(DATA_DIR, f"mouse_profile_{ts}.jsonl")
    sum_path = os.path.join(DATA_DIR, f"mouse_profile_{ts}_summary.json")

    print(f"📝 Recording for {duration_s:.0f}s @ {sample_hz:.0f} Hz")
    print(f"📄 Raw events -> {raw_path}")
    print(f"📄 Summary    -> {sum_path}")
    if qp_center:
        print(f"📍 Using orb center for relative stats: {qp_center}")
    else:
        print("ℹ️ No orb center calibrated; recording absolute movements only")

    quit_flag = {"stop": False}

    def on_key_press(key):
        try:
            if key.char == 'q':
                quit_flag["stop"] = True
                print("🛑 Quit requested")
                return False
        except AttributeError:
            pass

    kb_listener = keyboard.Listener(on_press=on_key_press)
    kb_listener.start()

    # Click listener
    click_events = []

    def on_click(x, y, button, pressed):
        click_events.append({
            "t": time.perf_counter(),
            "type": "click",
            "button": str(button),
            "pressed": bool(pressed),
            "x": int(x),
            "y": int(y),
        })

    m_listener = mouse.Listener(on_click=on_click)
    m_listener.start()

    # Sampling loop
    interval = 1.0 / sample_hz
    end_time = time.perf_counter() + duration_s

    last_pos = None
    last_emit_t = 0.0
    move_events = []

    try:
        while time.perf_counter() < end_time and not quit_flag["stop"]:
            now = time.perf_counter()
            x, y = pyautogui.position()
            pos = (int(x), int(y))
            if last_pos is None or pos != last_pos or (now - last_emit_t) >= 0.02:
                move_events.append({
                    "t": now,
                    "type": "move",
                    "x": pos[0],
                    "y": pos[1],
                })
                last_pos = pos
                last_emit_t = now
            # Targeted sleep
            sleep_left = interval - (time.perf_counter() - now)
            if sleep_left > 0:
                time.sleep(min(sleep_left, 0.01))
    finally:
        m_listener.stop()
        kb_listener.stop()

    # Persist raw events
    with open(raw_path, "w", encoding="utf-8") as f:
        for ev in move_events:
            f.write(json.dumps(ev) + "\n")
        for ev in click_events:
            f.write(json.dumps(ev) + "\n")

    # Build simple summary
    steps = []
    rel_steps = []
    for i in range(1, len(move_events)):
        a = move_events[i - 1]
        b = move_events[i]
        dt = max(1e-6, b["t"] - a["t"])  # seconds
        dx = b["x"] - a["x"]
        dy = b["y"] - a["y"]
        dist = math.hypot(dx, dy)
        steps.append({"dx": dx, "dy": dy, "ds": dist, "dt": dt})
        if qp_center:
            ra_dx = a["x"] - qp_center[0]
            ra_dy = a["y"] - qp_center[1]
            rb_dx = b["x"] - qp_center[0]
            rb_dy = b["y"] - qp_center[1]
            rel_steps.append({
                "r0": math.hypot(ra_dx, ra_dy),
                "r1": math.hypot(rb_dx, rb_dy),
                "dtheta": math.atan2(rb_dy, rb_dx) - math.atan2(ra_dy, ra_dx),
                "ds": dist,
                "dt": dt,
            })

    def simple_stats(vals):
        if not vals:
            return {"count": 0}
        return {
            "count": len(vals),
            "mean": sum(vals) / len(vals),
            "p50": sorted(vals)[len(vals) // 2],
            "p90": sorted(vals)[int(len(vals) * 0.9)],
            "p95": sorted(vals)[int(len(vals) * 0.95)],
            "max": max(vals),
        }

    speeds = [s["ds"] / s["dt"] for s in steps if s["dt"] > 0 and s["ds"] > 0]
    dists = [s["ds"] for s in steps]
    dts = [s["dt"] for s in steps]

    summary = {
        "duration_s": duration_s,
        "sample_hz": sample_hz,
        "num_moves": len(move_events),
        "num_click_events": len(click_events),
        "qp_center": qp_center,
        "step_distance": simple_stats(dists),
        "step_dt": simple_stats(dts),
        "speed_px_per_s": simple_stats(speeds),
    }

    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("✅ Recording complete")
    print(json.dumps(summary, indent=2))


def main():
    print("🎥 Human Movement Recorder (60s)")
    print("Move/click as you normally would on the orb. Press 'q' to stop early.")
    record(duration_s=60.0, sample_hz=240.0)


if __name__ == "__main__":
    main()


