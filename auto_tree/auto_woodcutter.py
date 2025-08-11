#!/usr/bin/env python3
"""
Auto Woodcutter - Complete AFK Woodcutting Bot
Automatically chops trees and manages inventory
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

def detect_player_position():
    """Detect the player's position by finding the orange tile (FFFF7D00)"""
    screen = capture_screen()
    
    # Convert to HSV for better color detection
    hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
    
    # Orange color range for player tile (FFFF7D00 = RGB 255, 125, 0)
    # HSV for orange: H=15-25, S=200-255, V=200-255
    lower_orange = np.array([10, 200, 200])
    upper_orange = np.array([30, 255, 255])
    
    # Create mask for orange color
    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Find the largest orange area (should be the player tile)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get the center of the player tile
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            player_x = int(M["m10"] / M["m00"])
            player_y = int(M["m01"] / M["m00"])
            return (player_x, player_y)
    
    return None

def find_tree_closest_to_player():
    """Find the tree indicator closest to the player's position - only consider substantial trees"""
    player_pos = detect_player_position()
    if not player_pos:
        return None
    
    trees = detect_tree_indicators()
    if not trees:
        return None
    
    # Filter out tiny tree indicators (likely artifacts) - only consider trees with reasonable size
    substantial_trees = [tree for tree in trees if tree['area'] >= 1000]  # Minimum 1000 pixel area
    
    if not substantial_trees:
        print("⚠️ No substantial trees found near player")
        return None
    
    player_x, player_y = player_pos
    closest_tree = None
    min_distance = float('inf')
    
    print(f"🎯 Player at ({player_x}, {player_y}), checking {len(substantial_trees)} substantial trees:")
    
    for i, tree in enumerate(substantial_trees):
        tree_x, tree_y = tree['position']
        distance = ((tree_x - player_x) ** 2 + (tree_y - player_y) ** 2) ** 0.5
        print(f"   Tree {i+1}: pos({tree_x}, {tree_y}), area {tree['area']:.0f}, distance {distance:.1f}px")
        
        if distance < min_distance:
            min_distance = distance
            closest_tree = tree
    
    if closest_tree:
        print(f"✅ Closest substantial tree: {closest_tree['position']} (distance: {min_distance:.1f}px, area: {closest_tree['area']:.0f})")
        return closest_tree
    
    return None

class AutoWoodcutter:
    def __init__(self):
        self.running = True
        self.paused = True  # Start paused
        self.current_tree = None
        self.trees_chopped = 0
        self.start_time = None
        self.tree_timeout = 30
        self.keyboard_listener = None
        self.inventory_manager = InventoryManager()
        self.logs_dropped = 0
        
        # Timing for periodic checks
        self.last_inventory_check = 0
        self.last_camera_rotation = 0
        self.inventory_check_interval = 20  # Check inventory every 20 seconds
        self.camera_rotation_interval = random.uniform(45, 60)  # Rotate camera every 45-60 seconds
        
    def start_keyboard_monitoring(self):
        """Start keyboard listener for hotkeys"""
        def on_key_press(key):
            try:
                if key.char == 'p':
                    self.paused = not self.paused
                    if self.paused:
                        print("\n⏸️  PAUSED - Press 'p' again to continue or 'q' to quit")
                    else:
                        print("\n▶️  UNPAUSED - Continuing woodcutting...")
                elif key.char == 'q':
                    print("\n🛑 Quit requested")
                    self.running = False
            except AttributeError:
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
            time.sleep(0.1)
            return True
        return True
    
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
            # Store detailed info about the exact tree we clicked
            self.current_tree = {
                'position': best_tree['position'],
                'area': best_tree['area'],
                'size': best_tree['size'],
                'bounding_box': best_tree['bounding_box']
            }
            print(f"✅ Tree clicked successfully! Tracking tree at {self.current_tree['position']} with area {self.current_tree['area']:.0f}")
            return best_tree
        else:
            print("❌ Failed to click tree")
            return None

    def find_and_click_closest_tree_to_player(self):
        """When current tree is gone, find and click the tree closest to player"""
        print("🔍 Current tree is gone - finding closest tree to player...")
        
        # Get fresh tree detection
        trees = detect_tree_indicators()
        if not trees:
            print("❌ No trees found for replacement")
            return None
        
        # Filter substantial trees only
        substantial_trees = [tree for tree in trees if tree['area'] >= 1000]
        if not substantial_trees:
            print("❌ No substantial trees found for replacement")
            return None
        
        # Find player position
        player_pos = detect_player_position()
        if not player_pos:
            print("❌ Could not detect player position")
            return None
        
        player_x, player_y = player_pos
        print(f"🎯 Player at ({player_x}, {player_y}), finding closest tree...")
        
        # Find the closest substantial tree to player
        closest_tree = None
        min_distance = float('inf')
        
        for tree in substantial_trees:
            tree_x, tree_y = tree['position']
            distance = ((tree_x - player_x) ** 2 + (tree_y - player_y) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_tree = tree
        
        if closest_tree:
            print(f"🎯 Closest tree: pos({closest_tree['position'][0]}, {closest_tree['position'][1]}), area {closest_tree['area']:.0f}, distance {min_distance:.1f}px")
            
            # Click the closest tree
            success = click_tree(closest_tree)
            if success:
                # Update our tracked tree
                self.current_tree = closest_tree
                print(f"✅ Successfully clicked closest tree to player!")
                return closest_tree
            else:
                print("❌ Failed to click closest tree")
                return None
        
        return None

    def rotate_camera(self):
        """Rotate the camera randomly to simulate human behavior"""
        # Random rotation direction and amount
        rotation_direction = random.choice(['left', 'right'])
        rotation_amount = random.uniform(0.3, 1.2)  # seconds to hold the key
        
        print(f"📹 Rotating camera {rotation_direction} for {rotation_amount:.1f}s")
        
        # Use arrow keys for camera rotation
        if rotation_direction == 'left':
            pyautogui.keyDown('left')
        else:
            pyautogui.keyDown('right')
        
        time.sleep(rotation_amount)
        
        # Release the key
        if rotation_direction == 'left':
            pyautogui.keyUp('left')
        else:
            pyautogui.keyUp('right')
        
        # Update last rotation time and set next interval
        self.last_camera_rotation = time.time()
        self.camera_rotation_interval = random.uniform(45, 60)
        print(f"📹 Camera rotated! Next rotation in {self.camera_rotation_interval:.0f}s")

    def check_periodic_tasks(self):
        """Check if it's time for inventory check or camera rotation"""
        current_time = time.time()
        
        # Check inventory every 20 seconds
        if current_time - self.last_inventory_check >= self.inventory_check_interval:
            print("🕒 Periodic inventory check...")
            try:
                inventory_managed = self.inventory_manager.manage_inventory()
                if inventory_managed:
                    self.logs_dropped += 1
                    print(f"✅ Inventory cleared during periodic check! Total drops: {self.logs_dropped}")
            except Exception as e:
                print(f"⚠️ Error during periodic inventory check: {e}")
            self.last_inventory_check = current_time
        
        # Rotate camera every 45-60 seconds
        if current_time - self.last_camera_rotation >= self.camera_rotation_interval:
            self.rotate_camera()
    
    def is_tree_still_there(self, original_tree, tolerance=50):
        """Check if the EXACT SPECIFIC tree we clicked is still present"""
        if not original_tree:
            return False
            
        current_trees = detect_tree_indicators()
        if not current_trees:
            print("    🔍 No trees detected at all - original tree is gone")
            return False
        
        orig_x, orig_y = original_tree['position']
        orig_area = original_tree['area']
        
        print(f"    🎯 Looking for original tree at ({orig_x}, {orig_y}) with area {orig_area:.0f}")
        
        # Find trees that match our EXACT original tree
        exact_matches = []
        close_trees = []
        
        for i, tree in enumerate(current_trees):
            tree_x, tree_y = tree['position']
            tree_area = tree['area']
            distance = ((tree_x - orig_x) ** 2 + (tree_y - orig_y) ** 2) ** 0.5
            
            # Very strict position matching - tree should be almost exactly where we clicked
            if distance <= tolerance:
                area_ratio = tree_area / orig_area
                close_trees.append(f"Tree #{i+1}: pos({tree_x}, {tree_y}), area {tree_area:.0f}, distance {distance:.1f}px, ratio {area_ratio:.3f}")
                
                # Very lenient area matching - walking, camera movement, and plugin effects change overlay
                if 0.50 <= area_ratio <= 1.50:
                    exact_matches.append({
                        'tree': tree,
                        'distance': distance,
                        'area_ratio': area_ratio,
                        'index': i+1
                    })
        
        if close_trees:
            print(f"    🔍 Found {len(close_trees)} trees within {tolerance}px:")
            for tree_info in close_trees[:3]:  # Only show first 3 close trees
                print(f"        {tree_info}")
        else:
            print(f"    🔍 No trees found within {tolerance}px of original position")
        
        if exact_matches:
            # Found our exact tree - it's still there
            best_match = min(exact_matches, key=lambda x: x['distance'])
            print(f"    ✅ Original tree FOUND - tree #{best_match['index']}, distance: {best_match['distance']:.1f}px, area ratio: {best_match['area_ratio']:.3f}")
            return True
        else:
            # No exact match found - but before giving up, check if there's ANY substantial tree near player
            print(f"    ❌ Original tree NOT FOUND - checking for any tree near player...")
            
            # Try to find any substantial tree close to player position
            player_pos = detect_player_position()
            if player_pos:
                player_x, player_y = player_pos
                
                # Look for ANY substantial tree near the player (within 100px)
                for tree in current_trees:
                    if tree['area'] >= 1000:  # Only substantial trees
                        tree_x, tree_y = tree['position']
                        distance_to_player = ((tree_x - player_x) ** 2 + (tree_y - player_y) ** 2) ** 0.5
                        
                        if distance_to_player <= 100:  # Within 100px of player
                            print(f"    🔄 Found substantial tree near player: pos({tree_x}, {tree_y}), area {tree['area']:.0f}, distance {distance_to_player:.1f}px")
                            print(f"    🖱️ Re-clicking tree to ensure it's being chopped...")
                            
                            # Click this tree to make sure we're actively chopping it
                            success = click_tree(tree)
                            if success:
                                # Update our tracked tree to this one
                                self.current_tree = tree
                                print(f"    ✅ Successfully re-clicked tree, now tracking this one")
                                return True
                            else:
                                print(f"    ❌ Failed to re-click tree")
            
            print(f"    ❌ No trees found near player - tree is definitely chopped down!")
            return False
    
    def wait_for_tree_to_disappear(self):
        """Wait for the current tree to be chopped down and disappear"""
        if not self.current_tree:
            return True
            
        print("⏳ Waiting for tree to be chopped down...")
        
        # STEP 1: Give the character time to WALK to the tree
        print("🚶 Allowing time for player to walk to tree...")
        time.sleep(5.0)  # Wait 5 seconds for player to walk
        
        if not self.check_if_should_continue():
            return False
        
        # STEP 2: Find the tree closest to the player (the one being chopped)
        print("🔍 Finding tree closest to player...")
        player_tree = find_tree_closest_to_player()
        if not player_tree:
            print("⚠️ Could not find tree near player, assuming original tree chopped")
            return True
        
        # Now track THIS tree (the one closest to player)
        self.current_tree = player_tree
        print(f"🎯 Now tracking tree at player location: {player_tree['position']}")
        
        start_wait = time.time()
        check_interval = 3.0  # Check every 3 seconds
        last_check = time.time()
        
        while self.running:
            current_time = time.time()
            
            if not self.check_if_should_continue():
                return False
                
            if self.paused:
                continue
                    
            # Check for periodic tasks (inventory and camera rotation)
            self.check_periodic_tasks()
            
            if current_time - last_check >= check_interval:
                still_there = self.is_tree_still_there(self.current_tree)
                
                if not still_there:
                    # Triple-check: wait and scan multiple times to be absolutely sure
                    print("🔍 Tree appears gone, triple-checking...")
                    
                    # First confirmation check
                    time.sleep(2.0)  # Wait longer for first check
                    confirmation_check_1 = self.is_tree_still_there(self.current_tree)
                    
                    if confirmation_check_1:
                        print("❌ First confirmation failed - tree is still there")
                        last_check = current_time
                        continue
                    
                    # Second confirmation check  
                    print("🔍 First check confirms gone, second check...")
                    time.sleep(2.0)  # Wait longer for second check
                    confirmation_check_2 = self.is_tree_still_there(self.current_tree)
                    
                    if confirmation_check_2:
                        print("❌ Second confirmation failed - tree is still there")
                        last_check = current_time
                        continue
                    
                    # Tree is definitely gone
                    elapsed = current_time - start_wait
                    print(f"🎉 Tree confirmed chopped down! (took {elapsed:.1f}s)")
                    self.trees_chopped += 1
                    self.current_tree = None
                    return True
                    
                elapsed = current_time - start_wait
                print(f"🌳 Tree still there... (waiting {elapsed:.1f}s)")
                last_check = current_time
            
            if current_time - start_wait > self.tree_timeout:
                print(f"⏰ Timeout waiting for tree! (waited {self.tree_timeout}s)")
                self.current_tree = None
                return True
                
            time.sleep(0.5)
            
        return False
    
    def run_woodcutting_loop(self):
        """Main woodcutting loop"""
        print("🪓 Auto Woodcutter - Complete AFK Bot")
        print("=" * 50)
        print("🤖 This bot will automatically:")
        print("   • Chop trees until inventory is full")
        print("   • Drop all logs when inventory reaches 28")  
        print("   • Continue chopping indefinitely")
        print()
        print("🎮 Controls:")
        print("   • Press 'p' to pause/unpause")
        print("   • Press 'q' to quit")
        print("   • Ctrl+C for emergency stop")
        print()
        print("⏸️  STARTING PAUSED - Press 'p' to begin woodcutting!")
        
        # Start keyboard monitoring
        self.start_keyboard_monitoring()
        
        # Wait for unpause
        while self.paused and self.running:
            time.sleep(0.1)
        
        if not self.running:
            return
            
        self.start_time = time.time()
        
        # Initialize periodic task timers
        self.last_inventory_check = self.start_time
        self.last_camera_rotation = self.start_time
        
        print("\n🚀 Starting automated woodcutting...")
        print(f"🕒 Periodic inventory checks every {self.inventory_check_interval}s")
        print(f"📹 Camera rotations every {self.camera_rotation_interval:.0f}s")
        
        try:
            cycle = 1
            while self.running:
                if not self.check_if_should_continue():
                    break
                    
                if self.paused:
                    continue
                
                print(f"\n--- Woodcutting Cycle #{cycle} ---")
                
                # Step 1: Check inventory and drop logs if full
                print("📦 Checking inventory...")
                inventory_managed = self.inventory_manager.manage_inventory()
                if inventory_managed:
                    self.logs_dropped += 1
                    print(f"✅ Inventory cleared! Total drops: {self.logs_dropped}")
                    
                    # Brief pause after dropping logs
                    time.sleep(random.uniform(1.0, 2.0))
                
                # Step 2: Find and click a tree
                # If we just chopped a tree, find closest to player; otherwise find best available
                if hasattr(self, '_tree_just_chopped') and self._tree_just_chopped:
                    tree = self.find_and_click_closest_tree_to_player()
                    self._tree_just_chopped = False  # Reset flag
                else:
                    tree = self.find_and_click_tree()
                
                if not tree:
                    print("⚠️  No trees available, waiting before retry...")
                    wait_time = random.uniform(3.0, 5.0)
                    start_wait = time.time()
                    while time.time() - start_wait < wait_time and self.running:
                        if not self.check_if_should_continue():
                            break
                        if not self.paused:
                            time.sleep(0.1)
                    continue
                
                # Step 3: Wait for tree to be chopped down
                tree_gone = self.wait_for_tree_to_disappear()
                
                if not tree_gone:
                    print("❌ Failed to detect tree removal")
                    continue
                
                # Tree was successfully chopped - set flag to find closest tree to player next
                self._tree_just_chopped = True
                
                # Step 4: Brief pause before next cycle
                wait_time = random.uniform(1.0, 2.5)
                print(f"💤 Brief pause ({wait_time:.1f}s) before next cycle...")
                start_pause = time.time()
                while time.time() - start_pause < wait_time and self.running:
                    if not self.check_if_should_continue():
                        break
                    if not self.paused:
                        time.sleep(0.1)
                
                # Print progress
                if self.start_time:
                    elapsed_minutes = (time.time() - self.start_time) / 60
                    rate = self.trees_chopped / elapsed_minutes if elapsed_minutes > 0 else 0
                    print(f"📊 Progress: {self.trees_chopped} trees chopped, {self.logs_dropped} inventory drops ({rate:.1f} trees/min)")
                
                cycle += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Emergency stop requested!")
            self.running = False
        finally:
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
                rate = (self.trees_chopped / total_time) * 3600
                logs_per_hour = (self.logs_dropped * 28 / total_time) * 3600
                print(f"   Trees per hour: {rate:.1f}")
                print(f"   Estimated logs/hour: {logs_per_hour:.0f}")

def main():
    """Main function - just run the woodcutter"""
    woodcutter = AutoWoodcutter()
    woodcutter.run_woodcutting_loop()

if __name__ == "__main__":
    main()