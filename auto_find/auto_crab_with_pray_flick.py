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
import random
from typing import Optional, Tuple

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pyautogui
from pynput import keyboard
from color_detection import capture_screen, TUNNEL_COLOR, CRAB_COLOR
import cv2
import numpy as np
 
# Import skill checking utilities
AUTO_ACTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'auto_actions')
sys.path.append(os.path.abspath(AUTO_ACTIONS_DIR))
try:
    from funcs import AutoActionFunctions
except Exception as e:
    AutoActionFunctions = None
    print(f"⚠️ Could not import AutoActionFunctions: {e}")

# Template-based tick digit detection (sequence-driven)
TICKS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'auto_actions', 'ticks')
sys.path.append(os.path.abspath(TICKS_DIR))
try:
    from tm_detect import (
        load_all_templates,
        classify_digit_from_frame,
    )
    TEMPLATES_DIR = os.path.join(TICKS_DIR, 'templates')
    ALL_TEMPLATES = load_all_templates(TEMPLATES_DIR)
    print(f"🧩 Loaded templates: all={ {k: len(v) for k,v in ALL_TEMPLATES.items()} }")
except Exception as e:
    ALL_TEMPLATES = {}
    print(f"⚠️ Tick detector unavailable: {e}")

# Pull HSV ranges from color_detection definitions to keep in sync
CYAN_RANGE = CRAB_COLOR['hsv_range']       # crab
MAGENTA_RANGE = TUNNEL_COLOR['hsv_range']  # tunnel

PAUSED = True
STOP = False
DEBUG = False
ROTATE_ENABLED = False  # disable camera rotation during testing; toggle with 'r'
FLICK_ON_AT_2_TO_1 = True  # True: ON at 2->1, OFF at 1->4. Toggle with 'o'
SCALE_X = 1.0
SCALE_Y = 1.0
TUNNEL_STABLE_FRAMES = 2
CRAB_STABLE_FRAMES = 1
CRAB_MISS_FRAMES_TO_EXIT = 4  # inner loop: require N consecutive misses before leaving

# Preferred skill to check during AFK (set based on current training)
PRIMARY_SKILL = 'strength'

# Quick-prayer toggle config
PRAY_TOGGLE_ENABLED = True
PRAY_MIN_COOLDOWN_MS = 200  # legacy; not used in flick loop
PRAY_SETTLE_MS_MIN = 70
PRAY_SETTLE_MS_MAX = 110
PRAY_HOLD_MS_MIN = 60
PRAY_HOLD_MS_MAX = 100
PRAY_MIN_CONF = 0.55

# Match flick test timings by default
USE_STATE_CHECK = False  # when True, verify orb state each frame (slower)
FLICK_COOLDOWN_MS = 160
FLICK_SETTLE_MIN = 50
FLICK_SETTLE_MAX = 90
FLICK_HOLD_MIN = 50
FLICK_HOLD_MAX = 85
FLICK_LOOP_SLEEP = 0.02

# Region validation for tunnel (avoid huge/edge blobs)
MAX_AREA_TUNNEL = 150000.0

# Test/behavior flags
RECLICK_CRAB_ENABLED = False  # disable periodic crab re-clicks during this flow


def on_key_press(key):
    global PAUSED, STOP, DEBUG, ROTATE_ENABLED, FLICK_ON_AT_2_TO_1
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
        elif key.char == 'r':
            ROTATE_ENABLED = not ROTATE_ENABLED
            print(f"🧭 Rotate {'ENABLED' if ROTATE_ENABLED else 'DISABLED'}")
        elif key.char == 'o':
            FLICK_ON_AT_2_TO_1 = not FLICK_ON_AT_2_TO_1
            orient = "ON at 2→1, OFF at 1→4" if FLICK_ON_AT_2_TO_1 else "OFF at 2→1, ON at 1→4"
            print(f"🔁 Flick orientation → {orient}")
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


def is_valid_tunnel_region(frame_shape, region, min_area: float, max_area: float) -> bool:
    if region is None:
        return False
    area = float(region[1])
    x, y, w, h = region[2]
    h_img, w_img = frame_shape[:2]
    if area < min_area or area > max_area:
        return False
    # Reject contours touching edges (common for false positives)
    if x <= 2 or y <= 2 or (x + w) >= (w_img - 2) or (y + h) >= (h_img - 2):
        return False
    return True


def detect_color(hsv, range_tuple):
    lower_hsv, upper_hsv = range_tuple
    mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)
    return find_largest_region(mask)


def click_at(point: Tuple[int, int]):
    global SCALE_X, SCALE_Y
    sys_w, sys_h = pyautogui.size()
    x = int(round(point[0] * SCALE_X))
    y = int(round(point[1] * SCALE_Y))
    # Clip to screen bounds to avoid off-screen moves
    x = max(0, min(sys_w - 1, x))
    y = max(0, min(sys_h - 1, y))
    pyautogui.moveTo(x, y, duration=0.2)
    time.sleep(0.02)
    pyautogui.click()


def humanized_middle_drag(total_dx: int, total_dy: int,
                          min_segments: int, max_segments: int,
                          duration_min: float, duration_max: float):
    """Perform a human-like middle-mouse drag composed of multiple jittered segments."""
    try:
        pyautogui.mouseDown(button='middle')
        segments = random.randint(min_segments, max_segments)
        # Total duration and segment weights
        total_duration = random.uniform(duration_min, duration_max)
        weights = [random.uniform(0.6, 1.4) for _ in range(segments)]
        weight_sum = sum(weights)
        # Distribute dx, dy across segments with small randomness
        remaining_dx = total_dx
        remaining_dy = total_dy
        for i in range(segments):
            # Proportion for this segment
            frac = weights[i] / weight_sum
            seg_dx = int(round(total_dx * frac))
            seg_dy = int(round(total_dy * frac))
            # Ensure we consume all by the last segment
            if i == segments - 1:
                seg_dx = remaining_dx
                seg_dy = remaining_dy
            # Add orthogonal jitter and slight curvature
            jitter_x = random.randint(-5, 5)
            jitter_y = random.randint(-3, 3)
            move_x = seg_dx + jitter_x
            move_y = seg_dy + jitter_y
            # Easing-like variable segment duration
            seg_duration = max(0.03, total_duration * frac * random.uniform(0.7, 1.3))
            pyautogui.moveRel(move_x, move_y, duration=seg_duration)
            # Micro pause occasionally
            if random.random() < 0.35:
                time.sleep(random.uniform(0.015, 0.05))
            remaining_dx -= seg_dx
            remaining_dy -= seg_dy
        # Small overshoot and correction to feel human
        overshoot_x = random.randint(4, 12) * (1 if total_dx >= 0 else -1)
        overshoot_y = random.randint(2, 8) * (1 if total_dy >= 0 else -1)
        pyautogui.moveRel(overshoot_x, overshoot_y, duration=random.uniform(0.04, 0.09))
        time.sleep(random.uniform(0.02, 0.05))
        pyautogui.moveRel(-int(overshoot_x * random.uniform(0.6, 1.0)),
                          -int(overshoot_y * random.uniform(0.6, 1.0)),
                          duration=random.uniform(0.04, 0.1))
    finally:
        pyautogui.mouseUp(button='middle')


def gentle_camera_rotate():
    # Hold middle mouse button and move mouse slightly to rotate camera with humanized motion
    try:
        dx = random.randint(90, 180) * random.choice([-1, 1])
        dy = random.randint(15, 45) * random.choice([-1, 1])
        humanized_middle_drag(dx, dy, min_segments=3, max_segments=5, duration_min=0.28, duration_max=0.6)
        print(f"🧭 Gentle rotate (middle) by approx ({dx},{dy})")
    except Exception as e:
        print(f"⚠️ Camera rotate failed: {e}")


def big_camera_rotate():
    # Larger camera rotation to reset perspective (middle mouse) with humanized motion
    try:
        dx = random.randint(240, 420) * random.choice([-1, 1])
        dy = random.randint(30, 90) * random.choice([-1, 1])
        humanized_middle_drag(dx, dy, min_segments=5, max_segments=8, duration_min=0.55, duration_max=1.1)
        print(f"🧭 Big rotate (middle) by approx ({dx},{dy})")
    except Exception as e:
        print(f"⚠️ Big camera rotate failed: {e}")


def half_turn_rotate():
    # Attempt a near-180° sweep using two phased humanized drags
    try:
        direction = random.choice([-1, 1])
        # Phase 1: long sweep
        dx1 = direction * random.randint(520, 880)
        dy1 = random.randint(30, 100) * random.choice([-1, 1])
        humanized_middle_drag(dx1, dy1, min_segments=6, max_segments=10, duration_min=0.9, duration_max=1.6)
        time.sleep(random.uniform(0.05, 0.12))
        # Phase 2: continuation sweep with slight opposite vertical drift
        dx2 = direction * random.randint(380, 680)
        dy2 = -int(dy1 * random.uniform(0.3, 0.9))
        humanized_middle_drag(dx2, dy2, min_segments=5, max_segments=9, duration_min=0.7, duration_max=1.4)
        # Small settle correction
        if random.random() < 0.6:
            settle_dx = -direction * random.randint(25, 60)
            settle_dy = random.randint(-20, 20)
            humanized_middle_drag(settle_dx, settle_dy, min_segments=2, max_segments=3, duration_min=0.15, duration_max=0.3)
        print("🧭 Performed near-180° camera sweep")
    except Exception as e:
        print(f"⚠️ Half-turn camera rotate failed: {e}")


def main():
    global PAUSED, STOP, DEBUG
    print("👀 Watch and Click - Cyan crab or Magenta tunnel")
    print("Hotkeys: p=toggle pause, s=pause, q=quit, d=debug")
    print("Click happens once per appearance; when it disappears and reappears, it will click again.")
    print("⏸️  PAUSED - Press 'p' to start")

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    # Optional auto actions for stats checking
    auto_funcs = AutoActionFunctions() if AutoActionFunctions is not None else None

    # Establish coordinate scaling between screenshot frames and OS screen
    try:
        probe = capture_screen()
        if probe is not None:
            frame_h, frame_w = probe.shape[:2]
            sys_w, sys_h = pyautogui.size()
            # Avoid division by zero
            if frame_w > 0 and frame_h > 0:
                # Scale detected frame coordinates to OS coordinates
                # Handles Windows DPI scaling / multi-monitor mismatch
                globals()['SCALE_X'] = float(sys_w) / float(frame_w)
                globals()['SCALE_Y'] = float(sys_h) / float(frame_h)
                if DEBUG:
                    print(f"🖥️ Scaling set: frame=({frame_w}x{frame_h}) screen=({sys_w}x{sys_h}) scale=({SCALE_X:.3f},{SCALE_Y:.3f})")
    except Exception as e:
        print(f"⚠️ Could not establish scaling: {e}")

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
    min_area_tunnel = 2200.0

    last_debug_time = 0.0

    # Background tasks timers
    start_time = time.time()
    last_forced_crab_click = start_time
    last_skills_check = start_time
    last_camera_rotate = start_time
    last_big_rotate = start_time
    last_equipment_check = start_time

    # Randomized base intervals (jitter added on each cycle)
    forced_crab_interval = random.uniform(28, 40)  # seconds
    skills_check_interval = random.uniform(90, 160)
    camera_rotate_interval = random.uniform(45, 90)
    big_rotate_interval = random.uniform(180, 360)
    half_turn_interval = random.uniform(600, 1200)
    equipment_check_interval = random.uniform(75, 150)

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
            # Stability counters to avoid flicker/false positives
            if not hasattr(main, "_crab_stable"):
                main._crab_stable = 0
                main._tunnel_stable = 0
            main._crab_stable = main._crab_stable + 1 if crab_visible else 0
            main._tunnel_stable = main._tunnel_stable + 1 if tunnel_visible else 0
            crab_ready = main._crab_stable >= CRAB_STABLE_FRAMES
            tunnel_ready = main._tunnel_stable >= TUNNEL_STABLE_FRAMES

            # Debug info every ~0.5s
            now = time.time()
            if DEBUG and now - last_debug_time > 0.5:
                crab_area = f"{crab[1]:.0f}" if crab else "0"
                tun_area = f"{tunnel[1]:.0f}" if tunnel else "0"
                print(f"🔎 crab_area={crab_area} (min {min_area_crab:.0f}), tunnel_area={tun_area} (min {min_area_tunnel:.0f})")
                last_debug_time = now

            # Debounced one-time click per continuous appearance
            now = time.time()

            # Prefer tunnel first at top-level (fresh validate), regardless of crab
            if tunnel_ready:
                tunnel_last_seen = now
                if not tunnel_clicked:
                    fresh_frame = capture_screen()
                    if fresh_frame is not None:
                        fresh_hsv = cv2.cvtColor(fresh_frame, cv2.COLOR_BGR2HSV)
                        tun_fresh = detect_color(fresh_hsv, MAGENTA_RANGE)
                        if is_valid_tunnel_region(fresh_frame.shape, tun_fresh, min_area_tunnel, MAX_AREA_TUNNEL):
                            (cx, cy), area, _ = tun_fresh
                            print(f"🎯 Clicking tunnel at ({cx},{cy}) area={area:.0f}")
                            click_at((cx, cy))
                            tunnel_clicked = True
                            # After clicking tunnel, start next iteration (look for crab next)
                            time.sleep(0.08)
                            continue
                        else:
                            if DEBUG:
                                why = 'none'
                                if tun_fresh is not None:
                                    why = f"area={tun_fresh[1]:.0f}, bbox={tun_fresh[2]}"
                                print(f"🔎 Tunnel invalid on refresh ({why}); skipping")

            # Update last-seen timestamps
            if crab_ready:
                crab_last_seen = now
                if not crab_clicked:
                    # Do not click crab if orange tick digits are visible (avoid interrupting flick)
                    if ALL_TEMPLATES:
                        try:
                            digit0, score0 = classify_digit_from_frame(frame, ALL_TEMPLATES, scales=(0.7,0.85,1.0,1.15))
                        except Exception:
                            digit0, score0 = (None, 0.0)
                        if digit0 is not None and score0 >= PRAY_MIN_CONF:
                            if DEBUG:
                                print(f"⏭️  Skip crab click: tick={digit0} score={score0:.2f}")
                            # Defer clicking this iteration
                            pass
                        else:
                            (cx, cy), area, _ = crab
                            print(f"🎯 Clicking crab at ({cx},{cy}) area={area:.0f}")
                            click_at((cx, cy))
                            crab_clicked = True
                    else:
                        (cx, cy), area, _ = crab
                        print(f"🎯 Clicking crab at ({cx},{cy}) area={area:.0f}")
                        click_at((cx, cy))
                        crab_clicked = True

                    # Engage loop: while crab visible and tunnel not visible, auto flick
                    if PRAY_TOGGLE_ENABLED and auto_funcs is not None and ALL_TEMPLATES:
                        last_toggle_ms = 0.0
                        print("🙏 Entering auto-prayer (ON at 2→1, OFF at 1→4)" if FLICK_ON_AT_2_TO_1 else "🙏 Entering auto-prayer (OFF at 2→1, ON at 1→4)")
                        seq_last = None
                        miss_frames = 0
                        while True:
                            if STOP or PAUSED:
                                break
                            frame2 = capture_screen()
                            if frame2 is None:
                                time.sleep(0.04)
                                continue
                            hsv2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2HSV)
                            # Update visibility to know when to leave
                            crab2 = detect_color(hsv2, CYAN_RANGE)
                            crab_vis2 = crab2 is not None and crab2[1] >= min_area_crab
                            # Require several consecutive misses before leaving
                            if crab_vis2:
                                miss_frames = 0
                            else:
                                miss_frames += 1
                                if miss_frames >= CRAB_MISS_FRAMES_TO_EXIT:
                                    break
                            now_ms = time.time() * 1000.0
                            # Transition-driven logic (robust): act on any 2->1 or 1->4 change
                            digit, score = classify_digit_from_frame(frame2, ALL_TEMPLATES, scales=(0.7,0.85,1.0,1.15))
                            if digit is not None and score >= PRAY_MIN_CONF and digit != seq_last:
                                prev = seq_last
                                seq_last = digit
                                # Check current orb state (if template provided)
                                state_on = False
                                if USE_STATE_CHECK:
                                    try:
                                        state_on = auto_funcs.is_quick_prayer_on(frame2)
                                    except Exception:
                                        state_on = False
                                if DEBUG:
                                    print(f"tick={digit} score={score:.2f}{' state='+('ON' if state_on else 'off') if USE_STATE_CHECK else ''}")
                                # Orientation switch (o): if FLICK_ON_AT_2_TO_1, ON at 2->1, OFF at 1->4; else reversed
                                if FLICK_ON_AT_2_TO_1 and prev == 2 and digit == 1 and (not USE_STATE_CHECK or not state_on) and (now_ms - last_toggle_ms) >= FLICK_COOLDOWN_MS:
                                    ok = auto_funcs.quick_prayer_toggle(
                                        use_mouse=True,
                                        settle_ms_min=FLICK_SETTLE_MIN,
                                        settle_ms_max=FLICK_SETTLE_MAX,
                                        hold_ms_min=FLICK_HOLD_MIN,
                                        hold_ms_max=FLICK_HOLD_MAX,
                                    )
                                    if ok:
                                        print("⚡ Toggle ON (2->1)")
                                        last_toggle_ms = now_ms
                                elif FLICK_ON_AT_2_TO_1 and prev == 1 and digit == 4 and (not USE_STATE_CHECK or state_on) and (now_ms - last_toggle_ms) >= FLICK_COOLDOWN_MS:
                                    ok = auto_funcs.quick_prayer_toggle(
                                        use_mouse=True,
                                        settle_ms_min=FLICK_SETTLE_MIN,
                                        settle_ms_max=FLICK_SETTLE_MAX,
                                        hold_ms_min=FLICK_HOLD_MIN,
                                        hold_ms_max=FLICK_HOLD_MAX,
                                    )
                                    if ok:
                                        print("⚡ Toggle OFF (1->4)")
                                        last_toggle_ms = now_ms
                                elif (not FLICK_ON_AT_2_TO_1) and prev == 2 and digit == 1 and (not USE_STATE_CHECK or state_on) and (now_ms - last_toggle_ms) >= FLICK_COOLDOWN_MS:
                                    ok = auto_funcs.quick_prayer_toggle(
                                        use_mouse=True,
                                        settle_ms_min=FLICK_SETTLE_MIN,
                                        settle_ms_max=FLICK_SETTLE_MAX,
                                        hold_ms_min=FLICK_HOLD_MIN,
                                        hold_ms_max=FLICK_HOLD_MAX,
                                    )
                                    if ok:
                                        print("⚡ Toggle OFF (2->1)")
                                        last_toggle_ms = now_ms
                                elif (not FLICK_ON_AT_2_TO_1) and prev == 1 and digit == 4 and (not USE_STATE_CHECK or not state_on) and (now_ms - last_toggle_ms) >= FLICK_COOLDOWN_MS:
                                    ok = auto_funcs.quick_prayer_toggle(
                                        use_mouse=True,
                                        settle_ms_min=FLICK_SETTLE_MIN,
                                        settle_ms_max=FLICK_SETTLE_MAX,
                                        hold_ms_min=FLICK_HOLD_MIN,
                                        hold_ms_max=FLICK_HOLD_MAX,
                                    )
                                    if ok:
                                        print("⚡ Toggle ON (1->4)")
                                        last_toggle_ms = now_ms
                            time.sleep(FLICK_LOOP_SLEEP)
            else:
                # Rearm only after sustained absence; but do not auto re-click repeatedly
                if crab_clicked and (now - crab_last_seen) >= rearm_absence_secs_crab:
                    crab_clicked = False

            if not tunnel_ready:
                if tunnel_clicked and (now - tunnel_last_seen) >= rearm_absence_secs_tunnel:
                    tunnel_clicked = False

            # Reactive rotation: gated by ROTATE_ENABLED
            if ROTATE_ENABLED and not crab_visible and not tunnel_visible:
                blind_duration = min(now - max(crab_last_seen, tunnel_last_seen), 999)
                if blind_duration > 4.0:
                    print("🔄 No targets seen for 4s — performing big rotate to search")
                    big_camera_rotate()
                    crab_last_seen = now
                    tunnel_last_seen = now
                elif blind_duration > 1.5:
                    print("🔄 No targets seen for 1.5s — rotating camera to search")
                    gentle_camera_rotate()
                    crab_last_seen = now
                    tunnel_last_seen = now

            # Periodic behaviors for AFK safety
            # 1) Re-click crab occasionally even if visible (to maintain aggro)
            if RECLICK_CRAB_ENABLED and (now - last_forced_crab_click > forced_crab_interval):
                if crab_visible:
                    (cx, cy), area, _ = crab
                    print(f"🔁 Periodic re-click on crab at ({cx},{cy}) area={area:.0f}")
                    click_at((cx, cy))
                last_forced_crab_click = now
                forced_crab_interval = random.uniform(28, 40)

            # 2) Occasionally rotate the camera slightly
            if now - last_camera_rotate > camera_rotate_interval:
                gentle_camera_rotate()
                last_camera_rotate = now
                camera_rotate_interval = random.uniform(45, 90)

            # 2b) Less frequent big rotate
            if now - last_big_rotate > big_rotate_interval:
                big_camera_rotate()
                last_big_rotate = now
                big_rotate_interval = random.uniform(180, 360)

            # 2c) Occasional near-180° sweep to reframe world
            if now - start_time > 30 and (now - start_time) % half_turn_interval < 1.0:
                # Ensure we don't trigger twice within the same window
                half_turn_interval = random.uniform(600, 1200)
                half_turn_rotate()

            # 3) Occasionally check skills
            if auto_funcs is not None and (now - last_skills_check > skills_check_interval):
                try:
                    # Prefer the primary training skill, sometimes check a related one
                    skill_pool = [PRIMARY_SKILL] * 3 + ['hitpoints', 'defence', 'attack', 'magic']
                    skill_choice = random.choice(skill_pool)
                    print(f"📊 Periodic skills check (pref {PRIMARY_SKILL}): {skill_choice}")
                    # Non-interactive so it won't pause the loop; quick action
                    auto_funcs.checkstats(skill_choice, method=random.choice(['keybind', 'tab']), interactive=False)
                except Exception as e:
                    print(f"⚠️ Skills check failed: {e}")
                finally:
                    last_skills_check = now
                    # Shorten interval a bit so you can notice it more
                    skills_check_interval = random.uniform(60, 120)

            # 4) Periodic work equipment check (key '5')
            if now - last_equipment_check > equipment_check_interval:
                try:
                    if auto_funcs is not None:
                        auto_funcs.press_key('5', 'work equipment check')
                    else:
                        print("🧰 Equipment check: pressing '5'")
                        pyautogui.press('5')
                except Exception as e:
                    print(f"⚠️ Equipment check failed: {e}")
                finally:
                    last_equipment_check = now
                    equipment_check_interval = random.uniform(75, 150)

            time.sleep(0.05)

    finally:
        listener.stop()
        print("👋 Stopped watcher")


if __name__ == "__main__":
    main()
