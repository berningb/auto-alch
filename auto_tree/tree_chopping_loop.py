#!/usr/bin/env python3
"""
Tree Chopping Loop - Automated Tree Cutting Bot
Clicks a tree, waits for it to be chopped down, then finds and clicks the next tree.
Perfect for AFK woodcutting training.
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
from tree_detector import detect_tree_indicators, capture_screen, click_tree
from inventory_manager import InventoryManager

class TreeChoppingBot:
    def __init__(self):
        self.running = True  # Start as True, will be set to False only when quitting
        self.paused = False
        self.current_tree = None
        self.trees_chopped = 0
        self.start_time = None
        self.last_tree_check = 0
        self.tree_timeout = 30  # Max seconds to wait for a tree to disappear
        self.keyboard_listener = None
        self.inventory_manager = InventoryManager()
        self.logs_dropped = 0
        
    def start_keyboard_monitoring(self):
        """Start keyboard listener for hotkeys"""
        def on_key_press(key):
            try:
                if key.char == 'p':
                    self.paused = not self.paused
                    if self.paused:
                        print("\n⏸️  PAUSED - Press 'p' again to continue or 'q' to quit")
                    else:
                        print("\n▶️  UNPAUSED - Continuing...")
                elif key.char == 'q':
                    print("\n🛑 Quit requested")
                    self.running = False
            except AttributeError:
                # Special keys (like ctrl, alt, etc.)
                pass
        
        self.keyboard_listener = keyboard.Listener(on_press=on_key_press)
        self.keyboard_listener.start()
        
    def stop_keyboard_monitoring(self):
        """Stop keyboard listener"""
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
        
    def check_if_should_continue(self):
        """Check if bot should continue running"""
        if not self.running:
            return False
        if self.paused:
            time.sleep(0.1)  # Small sleep when paused
            return True
        return True
        
    def wait_for_unpause(self, message="Press 'p' to start"):
        """Wait for user to press 'p' to unpause"""
        print(f"⏸️  PAUSED - {message}")
        print("    📝 Type 'p' in THIS TERMINAL and press Enter to continue")
        print("    📝 Type 'q' in THIS TERMINAL and press Enter to quit")
        print()
        
        while True:
            try:
                print("Waiting for input (p/q): ", end="", flush=True)
                key = input().strip().lower()
                if key == 'p':
                    print("▶️  UNPAUSED - Continuing...")
                    return True
                elif key == 'q':
                    print("🛑 Quit requested...")
                    self.running = False
                    return False
                else:
                    print("❌ Invalid input. Please type 'p' to continue or 'q' to quit")
            except KeyboardInterrupt:
                print("\n🛑 Quit requested via Ctrl+C...")
                self.running = False
                return False
        
    def find_and_click_tree(self):
        """Find and click on the best available tree"""
        print("🔍 Searching for trees...")
        
        trees = detect_tree_indicators()
        
        if not trees or len(trees) == 0:
            print("❌ No trees found")
            return None
            
        # Select the best tree (largest area = most prominent)
        best_tree = trees[0]
        
        print(f"🎯 Found {len(trees)} trees, targeting best one at {best_tree['position']}")
        
        # Click on the tree
        success = click_tree(best_tree)
        
        if success:
            self.current_tree = best_tree
            self.last_tree_check = time.time()
            print("✅ Tree clicked successfully!")
            return best_tree
        else:
            print("❌ Failed to click tree")
            return None
    
    def is_tree_still_there(self, original_tree, tolerance=40):
        """
        Check if the original tree is still present at its location
        Returns True if tree is still there, False if it's gone
        """
        if not original_tree:
            return False
            
        # Get current trees
        current_trees = detect_tree_indicators()
        
        if not current_trees:
            return False  # No trees means our tree is gone
        
        orig_x, orig_y = original_tree['position']
        orig_area = original_tree['area']
        
        # Check if any current tree is close to our original tree position
        matches_found = []
        for tree in current_trees:
            tree_x, tree_y = tree['position']
            distance = ((tree_x - orig_x) ** 2 + (tree_y - orig_y) ** 2) ** 0.5
            
            if distance <= tolerance:
                # Tree is close, check if it's similar size
                area_ratio = tree['area'] / orig_area
                if 0.6 <= area_ratio <= 1.4:  # Allow 40% size variation
                    matches_found.append({
                        'distance': distance,
                        'area_ratio': area_ratio,
                        'position': (tree_x, tree_y),
                        'area': tree['area']
                    })
        
        if matches_found:
            # Found potential matches - tree is likely still there
            best_match = min(matches_found, key=lambda x: x['distance'])
            return True
        
        return False  # Tree is gone!
    
    def wait_for_tree_to_disappear(self):
        """Wait for the current tree to be chopped down and disappear"""
        if not self.current_tree:
            return True
            
        print("⏳ Waiting for tree to be chopped down...")
        start_wait = time.time()
        check_interval = 2.0  # Check every 2 seconds
        last_check = time.time()
        
        while self.running:
            current_time = time.time()
            
            # Check if should continue (handles pause and quit)
            if not self.check_if_should_continue():
                return False
                
            # Skip if paused
            if self.paused:
                continue
                    
            # Check if tree is still there (every few seconds)
            if current_time - last_check >= check_interval:
                still_there = self.is_tree_still_there(self.current_tree)
                
                if not still_there:
                    # Double-check: wait a moment and scan again to confirm
                    print("🔍 Tree appears gone, double-checking...")
                    time.sleep(1.0)  # Wait 1 second
                    
                    # Re-check to confirm tree is really gone
                    confirmation_check = self.is_tree_still_there(self.current_tree)
                    
                    if not confirmation_check:
                        elapsed = current_time - start_wait
                        print(f"🎉 Tree confirmed chopped down! (took {elapsed:.1f}s)")
                        self.trees_chopped += 1
                        self.current_tree = None
                        return True
                    else:
                        print("❌ False positive - tree is still there, continuing to wait...")
                        last_check = current_time
                        continue
                    
                elapsed = current_time - start_wait
                print(f"🌳 Tree still there... (waiting {elapsed:.1f}s)")
                last_check = current_time
            
            # Timeout check
            if current_time - start_wait > self.tree_timeout:
                print(f"⏰ Timeout waiting for tree! (waited {self.tree_timeout}s)")
                print("   Tree might be depleted or we lost track of it")
                self.current_tree = None
                return True
                
            time.sleep(0.5)  # Small sleep to prevent excessive CPU usage
            
        return False
    
    def run_chopping_loop(self):
        """Main chopping loop"""
        print("🪓 Tree Chopping Loop Starting")
        print("=" * 50)
        print("This bot will:")
        print("• Find and click on trees")
        print("• Wait for each tree to be chopped down")
        print("• Automatically find and click the next tree")
        print("• Continue until stopped")
        print()
        print("Controls:")
        print("• Press 'p' to pause/unpause")
        print("• Press 'q' to quit")
        print("• Press Ctrl+C to emergency stop")
        print()
        
        continue_running = self.wait_for_unpause("Click into your game window, then press 'p' to start chopping")
        
        if not continue_running or not self.running:
            return
            
        # self.running is already True, just set start time
        self.start_time = time.time()
        print("🚀 Starting tree chopping automation...")
        
        # Start keyboard monitoring
        self.start_keyboard_monitoring()
        print("🎮 Controls now active:")
        print("   • Press 'p' key to pause/unpause anytime")
        print("   • Press 'q' key to quit anytime")
        print("   • Or use Ctrl+C for emergency stop")
        print()
        
        try:
            while self.running:
                # Check if should continue (handles pause and quit)
                if not self.check_if_should_continue():
                    break
                    
                # Skip if paused
                if self.paused:
                    continue
                
                # Step 0: Check inventory and drop logs if full
                print(f"\n--- Chopping Cycle #{self.trees_chopped + 1} ---")
                inventory_managed = self.inventory_manager.manage_inventory()
                if inventory_managed:
                    self.logs_dropped += 1
                    print(f"📊 Total log drops: {self.logs_dropped}")
                    
                    # Brief pause after dropping logs
                    time.sleep(random.uniform(1.0, 2.0))
                
                # Step 1: Find and click a tree
                tree = self.find_and_click_tree()
                
                if not tree:
                    print("⚠️  No trees available, waiting before retry...")
                    # Wait with pause checks
                    wait_time = random.uniform(3.0, 5.0)
                    start_wait = time.time()
                    while time.time() - start_wait < wait_time and self.running:
                        if not self.check_if_should_continue():
                            break
                        if not self.paused:  # Only sleep if not paused
                            time.sleep(0.1)
                    continue
                
                # Step 2: Wait for tree to be chopped down
                tree_gone = self.wait_for_tree_to_disappear()
                
                if not tree_gone:
                    print("❌ Failed to detect tree removal")
                    continue
                
                # Step 3: Brief pause before next tree
                wait_time = random.uniform(1.0, 2.5)
                print(f"💤 Brief pause ({wait_time:.1f}s) before next tree...")
                start_pause = time.time()
                while time.time() - start_pause < wait_time and self.running:
                    if not self.check_if_should_continue():
                        break
                    if not self.paused:  # Only sleep if not paused
                        time.sleep(0.1)
                
                # Print progress
                if self.start_time:
                    elapsed_minutes = (time.time() - self.start_time) / 60
                    rate = self.trees_chopped / elapsed_minutes if elapsed_minutes > 0 else 0
                    print(f"📊 Progress: {self.trees_chopped} trees chopped, {self.logs_dropped} inventory drops ({rate:.1f} trees/min)")
                
        except KeyboardInterrupt:
            print("\n🛑 Emergency stop requested!")
            self.running = False
        finally:
            # Clean up keyboard listener
            self.stop_keyboard_monitoring()
        
        # Final statistics
        if self.start_time:
            total_time = time.time() - self.start_time
            hours = int(total_time // 3600)
            minutes = int((total_time % 3600) // 60)
            seconds = int(total_time % 60)
            
            print(f"\n📈 Final Statistics:")
            print(f"   Trees chopped: {self.trees_chopped}")
            print(f"   Inventory drops: {self.logs_dropped}")
            print(f"   Time elapsed: {hours:02d}:{minutes:02d}:{seconds:02d}")
            if total_time > 0:
                rate = (self.trees_chopped / total_time) * 3600  # trees per hour
                logs_per_hour = (self.logs_dropped * 28 / total_time) * 3600  # approximate logs per hour
                print(f"   Average rate: {rate:.1f} trees/hour")
                print(f"   Estimated logs: {logs_per_hour:.0f} logs/hour")

# Removed the complex keyboard listener setup since we're using simple input() now

def main():
    """Main function"""
    print("🪓 Tree Chopping Bot")
    print("=" * 40)
    print("Automated woodcutting loop that:")
    print("• Detects trees using your Tree Indicator plugin")
    print("• Clicks on trees to start chopping")
    print("• Waits for trees to be chopped down")
    print("• Automatically finds the next tree")
    print()
    print("Prerequisites:")
    print("• Tree Indicator plugin must be enabled")
    print("• Trees must be visible on screen")
    print("• Character should be in a good woodcutting area")
    print()
    print("Choose mode:")
    print("1. Start tree chopping loop")
    print("2. Test tree detection only")
    print("3. Test inventory management")
    print("4. Exit")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        print("\n🪓 Starting tree chopping loop...")
        bot = TreeChoppingBot()
        bot.run_chopping_loop()
            
    elif choice == '2':
        print("\n🔍 Testing tree detection...")
        trees = detect_tree_indicators()
        if trees:
            print(f"✅ Found {len(trees)} trees:")
            for i, tree in enumerate(trees[:5]):
                print(f"   {i+1}. Position: {tree['position']}, Area: {tree['area']}")
        else:
            print("❌ No trees detected")
    
    elif choice == '3':
        print("\n📦 Testing inventory management...")
        inventory_manager = InventoryManager()
        if inventory_manager.log_template is not None:
            inventory_manager.test_log_detection()
        else:
            print("❌ Failed to load willow logs template")
            
    elif choice == '4':
        print("👋 Goodbye!")
        return
        
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
