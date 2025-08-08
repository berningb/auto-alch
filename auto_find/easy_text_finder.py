#!/usr/bin/env python3
"""
Easy Text Finder - Simple color-based text detection
Just finds and clicks on text elements without needing OCR
"""

import sys
import os
import time
import random

# Add the auto_actions directory to Python path so we can import funcs
auto_actions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auto_actions')
sys.path.append(auto_actions_dir)

try:
    import cv2
    import numpy as np
    import pyautogui
    from pynput import keyboard
    from funcs import AutoActionFunctions
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Install with: pip install opencv-python numpy pyautogui pynput")
    sys.exit(1)


def wait_for_unpause():
    """Wait for user to press 'p' to continue"""
    print("⏸️  PAUSED - Click into your game screen and press 'p' to start")
    
    is_paused = True
    
    def on_key_press(key):
        nonlocal is_paused
        try:
            if key.char == 'p':
                is_paused = False
                print("▶️  UNPAUSED - Starting action...")
                return False  # Stop listener
        except AttributeError:
            pass
    
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    
    while is_paused:
        time.sleep(0.1)
    
    listener.stop()


def findtextonscreen(target_text="text", color="white", click=True, pause=True):
    """
    Find text-like elements on screen by color and click on them
    
    Args:
        target_text (str): Name of what you're looking for (for display only)
        color (str): Color of text to find - "white", "yellow", "red", "green", "blue"
        click (bool): Whether to click on found text (default: True)
        pause (bool): Whether to pause and wait for 'p' key (default: True)
        
    Returns:
        dict: Result with success status and position
    """
    
    if pause:
        print(f"🔍 Looking for {color} text: '{target_text}'")
        wait_for_unpause()
    
    try:
        # Get screen capture
        functions = AutoActionFunctions()
        screen = functions.capture_screen()
        
        if screen is None:
            return {
                'success': False,
                'error': 'Failed to capture screen',
                'position': None
            }
        
        print(f"🎨 Searching for {color} text elements...")
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # Define color ranges (HSV format)
        color_ranges = {
            'white': [(0, 0, 200), (179, 30, 255)],      # Bright whites
            'yellow': [(20, 100, 100), (30, 255, 255)],  # Yellow text (like NPC names)
            'red': [(0, 120, 70), (10, 255, 255)],       # Red text (warnings, etc)
            'green': [(40, 40, 40), (80, 255, 255)],     # Green text
            'blue': [(100, 150, 0), (130, 255, 255)],    # Blue text
            'orange': [(10, 100, 100), (20, 255, 255)],  # Orange text
        }
        
        if color not in color_ranges:
            print(f"⚠️  Unknown color '{color}', using white")
            color = 'white'
        
        # Create color mask
        lower, upper = color_ranges[color]
        lower = np.array(lower)
        upper = np.array(upper)
        mask = cv2.inRange(hsv, lower, upper)
        
        # Find text-like shapes
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_elements = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Filter for text-like dimensions
            # Text is usually: not too small, not too big, reasonable width/height ratio
            if (8 < w < 300 and 
                6 < h < 60 and 
                area > 40 and 
                0.1 < h/w < 5):  # Width/height ratio
                
                center_x = x + w // 2
                center_y = y + h // 2
                
                text_elements.append({
                    'position': (center_x, center_y),
                    'size': (w, h),
                    'area': area
                })
                
                print(f"   ✅ Found {color} element at ({center_x}, {center_y}) size: {w}x{h}")
        
        if not text_elements:
            error_msg = f"No {color} text elements found"
            print(f"❌ {error_msg}")
            print(f"💡 Try different colors: white, yellow, red, green, blue, orange")
            return {
                'success': False,
                'error': error_msg,
                'position': None
            }
        
        # Click on the largest text element (usually most important)
        best_element = max(text_elements, key=lambda x: x['area'])
        position = best_element['position']
        
        print(f"🎯 Best {color} text element at {position} (size: {best_element['size']})")
        print(f"📊 Found {len(text_elements)} total {color} elements")
        
        if click:
            # Add some randomness to click position
            x, y = position
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-3, 3)
            final_x = x + offset_x
            final_y = y + offset_y
            
            print(f"🖱️  Moving to ({final_x}, {final_y}) and clicking...")
            pyautogui.moveTo(final_x, final_y, duration=0.3)
            time.sleep(0.2)
            pyautogui.click()
            time.sleep(0.1)
            print(f"✅ Successfully clicked on {color} text!")
        
        return {
            'success': True,
            'position': position,
            'size': best_element['size'],
            'color': color,
            'total_found': len(text_elements)
        }
        
    except Exception as e:
        error_msg = f"Error during text detection: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'position': None
        }


def quick_test():
    """Simple test function"""
    print("🔍 Easy Text Finder")
    print("=" * 40)
    print("This finds text by color - no OCR needed!")
    print()
    
    # Get what they're looking for
    target = input("What are you looking for? (e.g. 'Banker', 'Attack', 'Tunnel'): ").strip()
    if not target:
        target = "text"
    
    # Get color
    print("\nWhat color is the text?")
    print("Common choices:")
    print("  white  - Most interface text")
    print("  yellow - NPC names, item names")
    print("  red    - Damage, warnings")
    print("  green  - Success messages")
    print("  blue   - Links, special text")
    
    color = input("\nEnter color (default: yellow): ").strip().lower()
    if not color:
        color = "yellow"
    
    # Ask about clicking
    click_choice = input(f"\nClick on the {color} text when found? (y/n, default: y): ").strip().lower()
    should_click = click_choice != 'n'
    
    print(f"\n🎯 Ready to find {color} text: '{target}'")
    
    # Run the detection
    result = findtextonscreen(target, color=color, click=should_click)
    
    # Show results
    print(f"\n📊 Results:")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Position: {result['position']}")
        print(f"   Size: {result['size']}")
        print(f"   Total found: {result['total_found']}")
        if should_click:
            print(f"   ✅ Clicked successfully!")
    else:
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   💡 Try a different color or make sure the text is visible")


if __name__ == "__main__":
    quick_test()
