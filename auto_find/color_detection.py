#!/usr/bin/env python3
"""
Unified Color-Based Detection System
Replaces all template matching with reliable color detection
"""

import sys
import os
import time
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import pyautogui
from pynput import keyboard
import time

# ---- Helpers: pause control and screen capture ----

def wait_for_unpause():
    print("⏸️  PAUSED - Click into your game screen and press 'p' to start")
    is_paused = True

    def on_key_press(key):
        nonlocal is_paused
        try:
            if key.char == 'p':
                is_paused = False
                print("▶️  UNPAUSED - Starting action...")
                return False
        except AttributeError:
            pass

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    while is_paused:
        time.sleep(0.05)
    listener.stop()


def capture_screen():
    try:
        image = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return frame
    except Exception as e:
        print(f"❌ Error capturing screen: {e}")
        return None

# --------------------------------------------------

def detect_color_text(target_color, color_name, hsv_range):
    """
    Generic color detection for any colored text
    
    Args:
        target_color: Color name for display
        color_name: Color name for logging
        hsv_range: (lower_hsv, upper_hsv) tuple for color detection
    """
    print(f"🎨 Color Detection: {target_color}")
    print("=" * 40)
    print(f"Looking for {target_color} colored text")
    print()
    
    print(f"⏸️  Position your screen and press 'p' to detect {target_color} text...")
    wait_for_unpause()
    
    # Capture screen
    screen = capture_screen()
    if screen is None:
        print("❌ Failed to capture screen")
        return None
    
    print("✅ Screen captured, analyzing colors...")
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # Unpack HSV range
    lower_hsv, upper_hsv = hsv_range
    
    # Create mask for target color
    color_mask = cv2.inRange(hsv, lower_hsv, upper_hsv)
    
    # Optional: clean mask to reduce noise
    kernel = np.ones((3, 3), np.uint8)
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_DILATE, kernel, iterations=1)

    # Find contours (text regions)
    contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print(f"❌ No {target_color} text found")
        return None
    
    print(f"🔍 Found {len(contours)} {target_color} text regions")
    
    # Find the largest text region
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding box and center
    x, y, w, h = cv2.boundingRect(largest_contour)
    center_x = x + w // 2
    center_y = y + h // 2
    area = cv2.contourArea(largest_contour)
    
    print(f"✅ Largest {target_color} text found:")
    print(f"   Position: ({center_x}, {center_y})")
    print(f"   Size: {w}x{h}")
    print(f"   Area: {area} pixels")
    
    return {
        'success': True,
        'position': (center_x, center_y),
        'size': (w, h),
        'area': area,
        'bounding_box': (x, y, w, h),
        'color': color_name
    }


def click_color_text(target_color, color_name, hsv_range):
    """Detect and click on colored text"""
    print(f"🎯 {target_color} Text Clicker")
    print("=" * 30)
    
    result = detect_color_text(target_color, color_name, hsv_range)
    
    if result and result['success']:
        x, y = result['position']
        
        # Add small random offset
        offset_x = random.randint(-5, 5)
        offset_y = random.randint(-3, 3)
        final_x = x + offset_x
        final_y = y + offset_y
        
        print(f"🖱️  Moving to ({final_x}, {final_y}) and clicking...")
        pyautogui.moveTo(final_x, final_y, duration=0.25)
        time.sleep(0.05)
        pyautogui.click()
        time.sleep(0.1)
        
        print(f"✅ Successfully clicked on {target_color} text!")
        print(f"   Original position: {result['position']}")
        print(f"   Click position: ({final_x}, {final_y})")
        
        return {
            'success': True,
            'position': result['position'],
            'click_position': (final_x, final_y),
            'color': color_name
        }
    else:
        print(f"❌ No {target_color} text found")
        return {'success': False, 'error': f'No {target_color} text detected'}

# Color definitions (HSV)
# Tunnel color updated: #EF00FD (magenta). Widened HSV to be robust to lighting/AA.
# OpenCV H ≈ 148; use a broad window around 135–175, lower S/V floors to catch lighter text glows.
TUNNEL_COLOR = {
    'name': 'Magenta',
    'display': 'Magenta Tunnel',
    'hsv_range': (np.array([135, 80, 110]), np.array([175, 255, 255]))
}

# Cyan for crab label
CRAB_COLOR = {
    'name': 'Cyan',
    'display': 'Cyan Crab',
    'hsv_range': (np.array([80, 120, 120]), np.array([100, 255, 255]))
}


def clicktunnel():
    return click_color_text(
        TUNNEL_COLOR['display'], TUNNEL_COLOR['name'], TUNNEL_COLOR['hsv_range']
    )


def clickcrab():
    return click_color_text(
        CRAB_COLOR['display'], CRAB_COLOR['name'], CRAB_COLOR['hsv_range']
    )


def detect_tunnel():
    return detect_color_text(
        TUNNEL_COLOR['display'], TUNNEL_COLOR['name'], TUNNEL_COLOR['hsv_range']
    )


def detect_crab():
    return detect_color_text(
        CRAB_COLOR['display'], CRAB_COLOR['name'], CRAB_COLOR['hsv_range']
    )


def test_both_colors():
    print("🎨 Testing Both Color Detections")
    print("=" * 50)
    print("\n🕳️  Testing Magenta Tunnel Detection...")
    tunnel_result = detect_tunnel()
    if tunnel_result and tunnel_result['success']:
        print(f"✅ Tunnel detection: WORKING at {tunnel_result['position']}")
    else:
        print("❌ Tunnel detection: FAILED")

    print("\n🦀 Testing Cyan Crab Detection...")
    crab_result = detect_crab()
    if crab_result and crab_result['success']:
        print(f"✅ Crab detection: WORKING at {crab_result['position']}")
    else:
        print("❌ Crab detection: FAILED")


def main():
    print("🎨 Unified Color Detection System")
    print("=" * 50)
    print("Replaces all template matching with reliable color detection")
    print()
    print("Choose action:")
    print("1. Click tunnel (magenta)")
    print("2. Click crab (cyan)")
    print("3. Detect tunnel only")
    print("4. Detect crab only")
    print("5. Test both detections")
    print("6. Exit")
    print()

    choice = input("Enter choice (1-6): ").strip()

    if choice == '1':
        clicktunnel()
    elif choice == '2':
        clickcrab()
    elif choice == '3':
        detect_tunnel()
    elif choice == '4':
        detect_crab()
    elif choice == '5':
        test_both_colors()
    elif choice == '6':
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
