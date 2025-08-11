#!/usr/bin/env python3
"""
Inventory Manager - Handles inventory management for tree chopping bot
Detects logs, counts them, and drops when full
"""

import sys
import os
import time
import random
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import pyautogui

class InventoryManager:
    def __init__(self, log_template_path="../../willow_logs.png"):
        self.log_template_path = log_template_path
        self.log_template = None
        self.inventory_open = False
        self.max_logs = 28
        self.load_log_template()
        
    def load_log_template(self):
        """Load the willow logs template image"""
        try:
            self.log_template = cv2.imread(self.log_template_path)
            if self.log_template is None:
                print(f"❌ Failed to load log template from {self.log_template_path}")
                return False
            print(f"✅ Loaded willow logs template from {self.log_template_path}")
            return True
        except Exception as e:
            print(f"❌ Error loading log template: {e}")
            return False
    
    def open_inventory(self):
        """Press '0' to open inventory"""
        print("📦 Opening inventory...")
        pyautogui.press('0')
        time.sleep(0.5)  # Wait for inventory to open
        self.inventory_open = True
        
    def close_inventory(self):
        """Press Escape to close inventory"""
        print("📦 Closing inventory...")
        pyautogui.press('escape')
        time.sleep(0.3)
        self.inventory_open = False
        
    def capture_screen(self):
        """Capture current screen"""
        try:
            image = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"❌ Error capturing screen: {e}")
            return None
    
    def detect_logs(self, threshold=0.7):
        """
        Detect willow logs in inventory using template matching
        Returns list of log positions with confidence data
        """
        if self.log_template is None:
            print("❌ No log template loaded")
            return []
            
        # Capture screen
        screen = self.capture_screen()
        if screen is None:
            return []
        
        # Convert to grayscale for template matching
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(self.log_template, cv2.COLOR_BGR2GRAY)
        
        # Get template dimensions
        h, w = template_gray.shape
        
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
                'confidence': confidence
            })
        
        # Remove duplicate detections (group nearby positions)
        filtered_positions = self.filter_nearby_positions(log_positions, min_distance=30)
        
        return filtered_positions
    
    def filter_nearby_positions(self, positions, min_distance=30):
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
    
    def count_logs(self):
        """Count number of logs in inventory"""
        if not self.inventory_open:
            self.open_inventory()
        
        log_positions = self.detect_logs()
        log_count = len(log_positions)
        
        print(f"📊 Found {log_count} logs in inventory")
        return log_count, log_positions
    
    def get_dropping_pattern(self, log_positions):
        """Get logs in different dropping patterns for human-like behavior"""
        if not log_positions:
            return []
        
        # Create a copy to avoid modifying original
        positions = log_positions.copy()
        
        # Different dropping patterns
        patterns = [
            "random",           # Completely random
            "left_to_right",    # By column left to right
            "right_to_left",    # By column right to left
            "top_to_bottom",    # By row top to bottom
            "bottom_to_top",    # By row bottom to top
            "diagonal",         # Diagonal pattern
            "spiral",           # Spiral from outside in
        ]
        
        pattern = random.choice(patterns)
        print(f"🎲 Using dropping pattern: {pattern}")
        
        if pattern == "random":
            random.shuffle(positions)
        elif pattern == "left_to_right":
            positions.sort(key=lambda x: x['position'][0])  # Sort by x coordinate
        elif pattern == "right_to_left":
            positions.sort(key=lambda x: x['position'][0], reverse=True)
        elif pattern == "top_to_bottom":
            positions.sort(key=lambda x: x['position'][1])  # Sort by y coordinate
        elif pattern == "bottom_to_top":
            positions.sort(key=lambda x: x['position'][1], reverse=True)
        elif pattern == "diagonal":
            # Sort by distance from top-left corner
            positions.sort(key=lambda x: x['position'][0] + x['position'][1])
        elif pattern == "spiral":
            # Simple spiral approximation - sort by distance from center
            if positions:
                center_x = sum(pos['position'][0] for pos in positions) / len(positions)
                center_y = sum(pos['position'][1] for pos in positions) / len(positions)
                positions.sort(key=lambda x: ((x['position'][0] - center_x) ** 2 + (x['position'][1] - center_y) ** 2) ** 0.5, reverse=True)
        
        return positions

    def drop_logs(self, log_positions):
        """Drop logs by shift+left clicking on them in unpredictable patterns"""
        if not log_positions:
            print("❌ No logs to drop")
            return False
        
        print(f"🗑️  Dropping {len(log_positions)} logs...")
        
        # Get logs in a random dropping pattern
        ordered_positions = self.get_dropping_pattern(log_positions)
        
        for i, log_data in enumerate(ordered_positions):
            x, y = log_data['position']
            confidence = log_data['confidence']
            
            print(f"   Dropping log {i+1}/{len(ordered_positions)} at ({x}, {y}) - confidence: {confidence:.3f}")
            
            # Add small random offset to make clicks more natural
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            final_x = x + offset_x
            final_y = y + offset_y
            
            # Shift + left click to drop
            pyautogui.keyDown('shift')
            time.sleep(0.05)
            pyautogui.click(final_x, final_y)
            time.sleep(0.1)
            pyautogui.keyUp('shift')
            
            # Small delay between drops with more variation
            time.sleep(random.uniform(0.15, 0.5))
        
        print("✅ All logs dropped!")
        return True
    
    def is_inventory_full(self):
        """Check if inventory is full (28+ logs)"""
        log_count, _ = self.count_logs()
        return log_count >= self.max_logs
    
    def manage_inventory(self):
        """
        Main inventory management function
        Returns True if inventory was managed, False if no action needed
        """
        print("\n📦 Checking inventory status...")
        
        # First, check if logs are visible (inventory might already be open)
        print("📦 Checking if inventory is already open...")
        log_count, log_positions = self.count_logs()
        
        # If no logs found, inventory might be closed - try opening it
        if log_count == 0:
            print("📦 No logs detected - opening inventory...")
            self.open_inventory()
            
            # Check again after opening
            log_count, log_positions = self.count_logs()
        else:
            print("📦 Inventory appears to be already open")
            self.inventory_open = True
        
        if log_count >= self.max_logs:
            print(f"🔴 Inventory full! ({log_count}/{self.max_logs} logs)")
            
            # Drop all logs
            success = self.drop_logs(log_positions)
            
            if success:
                # Wait a moment for drops to process
                time.sleep(1.0)
                
                # Verify logs were dropped
                new_count, _ = self.count_logs()
                print(f"📊 After dropping: {new_count} logs remaining")
                
                # Close inventory
                self.close_inventory()
                return True
            else:
                print("❌ Failed to drop logs")
                self.close_inventory()
                return False
        else:
            print(f"🟢 Inventory OK ({log_count}/{self.max_logs} logs)")
            self.close_inventory()
            return False
    
    def test_log_detection(self):
        """Test log detection without dropping"""
        print("🧪 Testing log detection...")
        
        self.open_inventory()
        time.sleep(1.0)
        
        log_count, log_positions = self.count_logs()
        
        print(f"📊 Detection results:")
        print(f"   Logs found: {log_count}")
        
        if log_positions:
            print("📍 Log positions:")
            for i, log_data in enumerate(log_positions):
                x, y = log_data['position']
                confidence = log_data['confidence']
                print(f"   {i+1}. ({x}, {y}) - confidence: {confidence:.3f}")
        
        self.close_inventory()
        return log_count, log_positions

def main():
    """Test the inventory manager"""
    print("📦 Inventory Manager Test")
    print("=" * 40)
    
    manager = InventoryManager()
    
    if manager.log_template is None:
        print("❌ Failed to load log template - cannot continue")
        return
    
    print("Choose test:")
    print("1. Test log detection only")
    print("2. Test full inventory management")
    print("3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        print("\n🧪 Testing log detection...")
        manager.test_log_detection()
        
    elif choice == '2':
        print("\n📦 Testing inventory management...")
        manager.manage_inventory()
        
    elif choice == '3':
        print("👋 Goodbye!")
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()

