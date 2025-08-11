#!/usr/bin/env python3
"""
Test Inventory - Simple test for detecting and shift-clicking willow logs
"""

import sys
import os
import time
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import pyautogui
from inventory_manager import InventoryManager

def capture_screen():
    """Capture current screen"""
    try:
        image = pyautogui.screenshot()
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        return frame
    except Exception as e:
        print(f"❌ Error capturing screen: {e}")
        return None

def load_willow_template():
    """Load willow logs template"""
    template_path = "../../willow_logs.png"
    
    try:
        template = cv2.imread(template_path)
        if template is None:
            print(f"❌ Failed to load template from {template_path}")
            return None
        print(f"✅ Loaded willow logs template from {template_path}")
        return template
    except Exception as e:
        print(f"❌ Error loading template: {e}")
        return None

def detect_willow_logs(threshold=0.7):
    """Detect willow logs in current screen"""
    template = load_willow_template()
    if template is None:
        return []
    
    # Capture screen
    screen = capture_screen()
    if screen is None:
        return []
    
    print("🔍 Analyzing screen for willow logs...")
    
    # Convert to grayscale
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # Get template dimensions
    h, w = template_gray.shape
    print(f"📏 Template size: {w}x{h} pixels")
    
    # Perform template matching
    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    
    # Find all matches above threshold
    locations = np.where(result >= threshold)
    
    # Convert to list of positions with confidence scores
    log_positions = []
    for pt in zip(*locations[::-1]):  # Switch x and y
        center_x = pt[0] + w // 2
        center_y = pt[1] + h // 2
        confidence = result[pt[1], pt[0]]
        log_positions.append({
            'position': (center_x, center_y),
            'confidence': confidence,
            'box': (pt[0], pt[1], w, h)
        })
    
    # Remove duplicate detections (group nearby positions)
    filtered_positions = filter_nearby_positions(log_positions, min_distance=30)
    
    print(f"🎯 Found {len(filtered_positions)} willow log matches")
    
    return filtered_positions

def filter_nearby_positions(positions, min_distance=30):
    """Remove duplicate positions that are too close together"""
    if not positions:
        return []
    
    # Sort by confidence (highest first)
    positions.sort(key=lambda x: x['confidence'], reverse=True)
    
    filtered = []
    for pos in positions:
        x, y = pos['position']
        too_close = False
        
        for existing in filtered:
            ex_x, ex_y = existing['position']
            distance = ((x - ex_x)**2 + (y - ex_y)**2)**0.5
            if distance < min_distance:
                too_close = True
                break
                
        if not too_close:
            filtered.append(pos)
    
    return filtered

def open_inventory():
    """Press '0' to open inventory"""
    print("📦 Opening inventory (pressing '0')...")
    pyautogui.press('0')
    time.sleep(0.8)  # Wait for inventory to open

def close_inventory():
    """Press Escape to close inventory"""
    print("📦 Closing inventory (pressing Escape)...")
    pyautogui.press('escape')
    time.sleep(0.5)

def shift_click_logs(log_positions):
    """Shift+left click on detected logs to drop them"""
    if not log_positions:
        print("❌ No logs to click")
        return
    
    print(f"🖱️  Shift+clicking {len(log_positions)} logs...")
    
    for i, log_data in enumerate(log_positions):
        x, y = log_data['position']
        confidence = log_data['confidence']
        
        print(f"   {i+1}. Clicking log at ({x}, {y}) - confidence: {confidence:.3f}")
        
        # Add small random offset to make clicks more natural
        offset_x = random.randint(-3, 3)
        offset_y = random.randint(-3, 3)
        final_x = x + offset_x
        final_y = y + offset_y
        
        # Shift + left click
        pyautogui.keyDown('shift')
        time.sleep(0.05)
        pyautogui.click(final_x, final_y)
        time.sleep(0.1)
        pyautogui.keyUp('shift')
        
        # Small delay between clicks
        time.sleep(random.uniform(0.2, 0.4))
    
    print("✅ Finished clicking all logs!")

def test_detection_only():
    """Test detection without opening inventory"""
    print("\n🧪 Testing Detection Only")
    print("=" * 40)
    print("This will detect logs in whatever is currently on screen")
    
    input("Press Enter when ready to detect...")
    
    logs = detect_willow_logs()
    
    if logs:
        print(f"\n✅ Found {len(logs)} logs:")
        for i, log_data in enumerate(logs):
            x, y = log_data['position']
            confidence = log_data['confidence']
            print(f"   {i+1}. Position: ({x}, {y}) - Confidence: {confidence:.3f}")
    else:
        print("\n❌ No logs detected")

def test_full_process():
    """Test the full process: open inventory, detect logs, shift-click them"""
    print("\n🔄 Testing Full Process with Randomized Dropping")
    print("=" * 50)
    print("This will:")
    print("1. Open inventory")
    print("2. Detect willow logs")
    print("3. Drop them using random pattern")
    print("4. Close inventory")
    
    input("Press Enter when ready to start...")
    
    # Create inventory manager
    inventory_mgr = InventoryManager()
    
    # Step 1: Open inventory
    print("📦 Opening inventory...")
    inventory_mgr.open_inventory()
    
    # Step 2 & 3: Count logs and drop if found
    log_count, log_positions = inventory_mgr.count_logs()
    
    if log_positions:
        print(f"\n✅ Found {len(log_positions)} logs in inventory")
        
        # Step 3: Drop logs using randomized pattern
        inventory_mgr.drop_logs(log_positions)
        
        # Wait a moment
        time.sleep(1.0)
        
        # Step 4: Check if logs were dropped (re-detect)
        print("\n🔍 Checking if logs were dropped...")
        remaining_count, _ = inventory_mgr.count_logs()
        print(f"📊 Logs remaining: {remaining_count}")
        
    else:
        print("\n❌ No logs found in inventory")
    
    # Step 5: Close inventory
    print("📦 Closing inventory...")
    inventory_mgr.close_inventory()

def main():
    """Main test menu"""
    print("🧪 Willow Logs Detection & Drop Test")
    print("=" * 50)
    print("Test willow log detection and shift-clicking")
    print()
    print("Choose test:")
    print("1. Test detection only (current screen)")
    print("2. Test full process (open inventory, detect, drop)")
    print("3. Exit")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == '1':
        test_detection_only()
        
    elif choice == '2':
        test_full_process()
        
    elif choice == '3':
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()

