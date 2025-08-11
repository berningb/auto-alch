#!/usr/bin/env python3
"""
Tree Detector - Detects and clicks trees highlighted by Fiish's Tree Indicator RuneLite plugin
Uses color detection to find the green tree indicator overlays and clicks on them.
"""

import sys
import os
import time
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'auto_find'))

import cv2
import numpy as np
import pyautogui
from pynput import keyboard

def wait_for_unpause():
    """Wait for user to press 'p' to unpause"""
    print("⏸️  PAUSED - Click into your game screen and press 'p' to start")
    is_paused = True

    def on_key_press(key):
        nonlocal is_paused
        try:
            if key.char == 'p':
                is_paused = False
                print("▶️  UNPAUSED - Starting tree detection...")
                return False
        except AttributeError:
            pass

    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    while is_paused:
        time.sleep(0.05)
    listener.stop()

def capture_screen():
    """Capture current screen"""
    try:
        image = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return frame
    except Exception as e:
        print(f"❌ Error capturing screen: {e}")
        return None

def detect_tree_indicators(debug=False):
    """
    Detect tree indicator overlays from the RuneLite plugin
    Default color is green: RGB(0, 200, 120) = #00C878
    """
    print("🌳 Tree Indicator Detection")
    print("=" * 40)
    print("Looking for green tree indicator overlays")
    print("Make sure your Tree Indicator plugin is enabled!")
    print()
    
    # Capture screen
    screen = capture_screen()
    if screen is None:
        print("❌ Failed to capture screen")
        return None
    
    print("✅ Screen captured, analyzing for tree indicators...")
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # Tree indicator green color - expanded range to catch different shades
    # Based on the screenshot, the green appears brighter and more saturated
    # Using a wider HSV range to catch various green tree indicators
    lower_green = np.array([35, 100, 100])   # Lower bound - catches darker greens
    upper_green = np.array([85, 255, 255])   # Upper bound - catches brighter greens
    
    # Create mask for tree indicator color
    tree_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Clean up the mask to reduce noise
    kernel = np.ones((3, 3), np.uint8)
    tree_mask = cv2.morphologyEx(tree_mask, cv2.MORPH_OPEN, kernel, iterations=1)
    tree_mask = cv2.morphologyEx(tree_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Debug: Save mask image if requested
    if debug:
        cv2.imwrite("debug_tree_mask.png", tree_mask)
        print("🐛 Debug: Saved mask to debug_tree_mask.png")
    
    # Find contours (tree indicator regions)
    contours, _ = cv2.findContours(tree_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("❌ No tree indicators found")
        print("   - Make sure Tree Indicator plugin is enabled")
        print("   - Check that trees are visible on screen")
        print("   - Verify the indicator color matches (default green)")
        return None
    
    print(f"🔍 Found {len(contours)} tree indicator regions")
    
    # Filter contours by area to remove noise
    min_area = 50  # Minimum area for a valid tree indicator
    valid_trees = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area >= min_area:
            # Get bounding box and center
            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            
            valid_trees.append({
                'position': (center_x, center_y),
                'size': (w, h),
                'area': area,
                'bounding_box': (x, y, w, h)
            })
    
    if not valid_trees:
        print("❌ No valid tree indicators found (all too small)")
        return None
    
    # Sort by area (largest first - usually the closest/most prominent tree)
    valid_trees.sort(key=lambda t: t['area'], reverse=True)
    
    print(f"✅ Found {len(valid_trees)} valid tree indicators:")
    for i, tree in enumerate(valid_trees[:5]):  # Show top 5
        print(f"   {i+1}. Position: {tree['position']}, Area: {tree['area']} pixels")
    
    return valid_trees

def click_tree(tree_info):
    """Click on a detected tree with random offset"""
    if not tree_info:
        return False
    
    x, y = tree_info['position']
    
    # Add random offset to make clicks more natural
    offset_x = random.randint(-10, 10)
    offset_y = random.randint(-8, 8)
    final_x = x + offset_x
    final_y = y + offset_y
    
    print(f"🖱️  Clicking tree at ({final_x}, {final_y})")
    print(f"   Original center: ({x}, {y})")
    print(f"   Random offset: ({offset_x}, {offset_y})")
    
    try:
        pyautogui.moveTo(final_x, final_y, duration=0.2)
        time.sleep(0.05)
        pyautogui.click()
        time.sleep(0.1)
        return True
    except Exception as e:
        print(f"❌ Error clicking: {e}")
        return False

def detect_and_click_tree():
    """Main function to detect and click the best tree"""
    print("🌳 Tree Auto-Clicker")
    print("=" * 30)
    print("This will detect and click on trees highlighted by your Tree Indicator plugin")
    print()
    
    # Wait for user to be ready
    print("⏸️  Position your screen to show trees and press 'p' to start...")
    wait_for_unpause()
    
    # Detect trees
    trees = detect_tree_indicators()
    
    if trees and len(trees) > 0:
        # Click on the largest/most prominent tree
        best_tree = trees[0]
        print(f"\n🎯 Targeting best tree at {best_tree['position']}")
        
        success = click_tree(best_tree)
        
        if success:
            print("✅ Successfully clicked on tree!")
            return {
                'success': True,
                'position': best_tree['position'],
                'trees_found': len(trees)
            }
        else:
            print("❌ Failed to click on tree")
            return {'success': False, 'error': 'Click failed'}
    else:
        print("❌ No trees detected")
        return {'success': False, 'error': 'No trees found'}

def test_detection_only():
    """Test tree detection without clicking"""
    print("🔍 Tree Detection Test Mode")
    print("=" * 30)
    print("This will only detect trees, no clicking")
    print()
    
    print("⏸️  Position your screen and press 'p' to test detection...")
    wait_for_unpause()
    
    trees = detect_tree_indicators()
    
    if trees and len(trees) > 0:
        print(f"\n✅ Detection successful! Found {len(trees)} trees")
        print("Top trees detected:")
        for i, tree in enumerate(trees[:3]):  # Show top 3
            print(f"   {i+1}. Position: {tree['position']}, Area: {tree['area']} pixels")
        return trees
    else:
        print("\n❌ No trees detected")
        return None

def continuous_tree_clicking():
    """Continuously detect and click trees with delay"""
    print("🔄 Continuous Tree Clicking Mode")
    print("=" * 40)
    print("This will continuously search for and click trees")
    print("Press Ctrl+C to stop")
    print()
    
    print("⏸️  Position your screen and press 'p' to start continuous mode...")
    wait_for_unpause()
    
    click_count = 0
    
    try:
        while True:
            print(f"\n--- Scan #{click_count + 1} ---")
            
            trees = detect_tree_indicators()
            
            if trees and len(trees) > 0:
                best_tree = trees[0]
                success = click_tree(best_tree)
                
                if success:
                    click_count += 1
                    print(f"✅ Tree clicked! Total clicks: {click_count}")
                else:
                    print("❌ Click failed")
            else:
                print("⏳ No trees found, waiting...")
            
            # Wait before next scan
            wait_time = random.uniform(2.0, 4.0)  # Random delay between 2-4 seconds
            print(f"💤 Waiting {wait_time:.1f}s before next scan...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Stopping continuous mode. Total trees clicked: {click_count}")

def main():
    """Main menu"""
    print("🌳 Tree Detector & Auto-Clicker")
    print("=" * 50)
    print("Detects trees highlighted by Fiish's Tree Indicator RuneLite plugin")
    print()
    print("Prerequisites:")
    print("• Tree Indicator plugin must be enabled")
    print("• Trees must be visible on screen")
    print("• Default green color (RGB 0,200,120)")
    print()
    print("Choose action:")
    print("1. Detect and click best tree (once)")
    print("2. Test detection only (no clicking)")
    print("3. Continuous tree clicking")
    print("4. Debug mode (saves detection mask)")
    print("5. Exit")
    print()
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == '1':
        print("\n🎯 Single tree click mode")
        result = detect_and_click_tree()
        if result['success']:
            print(f"✅ Success! Found {result['trees_found']} trees, clicked best one")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    elif choice == '2':
        print("\n🔍 Detection test mode")
        trees = test_detection_only()
        if trees:
            print(f"✅ Test successful! {len(trees)} trees detected")
        else:
            print("❌ Test failed - no trees detected")
    
    elif choice == '3':
        print("\n🔄 Continuous clicking mode")
        continuous_tree_clicking()
    
    elif choice == '4':
        print("\n🐛 Debug mode")
        print("This will save a debug image showing what colors are detected")
        input("Press Enter when ready...")
        trees = detect_tree_indicators(debug=True)
        if trees:
            print(f"✅ Debug complete! Found {len(trees)} trees")
            print("Check debug_tree_mask.png to see what was detected")
        else:
            print("❌ No trees detected - check debug_tree_mask.png")
    
    elif choice == '5':
        print("👋 Goodbye!")
        return
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
