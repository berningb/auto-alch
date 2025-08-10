#!/usr/bin/env python3
"""
Simple Dart Detection Test using find_item method with clicking
"""

import cv2
import numpy as np
import pyautogui
import time
import os
import glob
import random

class DartTester:
    def __init__(self):
        self.dart_templates = self.load_item_templates("dart")
        self.debug = True
        
        # Configure pyautogui for safety
        pyautogui.FAILSAFE = True  # Move mouse to corner to stop
        pyautogui.PAUSE = 0.1  # Small pause between actions
    
    def load_item_templates(self, item_name):
        """Load all templates for a given item name from images directory"""
        templates = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(current_dir, "images")
        
        # Look for files matching the pattern: item_name*.png
        pattern = os.path.join(images_dir, f"{item_name}*.png")
        template_files = glob.glob(pattern)
        
        # Also check current directory
        current_pattern = os.path.join(current_dir, f"{item_name}*.png")
        template_files.extend(glob.glob(current_pattern))
        
        # Remove duplicates and sort for consistent ordering
        template_files = sorted(list(set(template_files)))
        
        for template_file in template_files:
            try:
                template = cv2.imread(template_file)
                if template is not None:
                    templates.append(template)
                    filename = os.path.basename(template_file)
                    print(f"✅ Loaded {item_name} template: {filename}")
                else:
                    print(f"❌ Failed to load {template_file}")
            except Exception as e:
                print(f"❌ Error loading {template_file}: {e}")
        
        return templates
    
    def find_template(self, screen, template, threshold=0.7):
        """Find template in screen using template matching"""
        try:
            if template is None:
                return None, 0
            
            # Convert to grayscale
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template_gray.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y), max_val
            else:
                return None, max_val
                
        except Exception as e:
            print(f"Error in template matching: {e}")
            return None, 0
    
    def find_item(self, screen, item_name, threshold=0.55, use_color_fallback=False):
        """Generic method to find any item using template matching and optional color fallback"""
        templates = getattr(self, f"{item_name}_templates", [])
        if not templates:
            print(f"❌ No templates available for {item_name}")
            return None, 0.0
        
        # 1) Template matching with all available templates
        best_result = None
        best_confidence = 0.0
        best_template_index = -1
        
        for i, template in enumerate(templates):
            result, confidence = self.find_template(screen, template, threshold=threshold)
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = result
                best_template_index = i
        
        # Return template match if any template has good confidence
        if best_confidence >= threshold and best_result:
            if self.debug:
                print(f"   📊 Using {item_name} template {best_template_index + 1} (confidence: {best_confidence:.2f})")
            return best_result, best_confidence
        
        # Return template match even if below threshold, but don't use color fallback
        if self.debug and best_confidence > 0.3:
            print(f"   📊 Best {item_name} template match: {best_confidence:.2f} (need ≥ {threshold})")
        return None, best_confidence
    
    def find_darts(self, screen):
        """Find darts using the generic find_item method"""
        return self.find_item(screen, "dart", threshold=0.55, use_color_fallback=False)
    
    def add_click_variation(self, position, base_range: tuple | None = None):
        """Add random variation to click position"""
        x, y = position
        
        # Choose base variation window
        if base_range is None:
            base_min, base_max = 3, 8
        else:
            base_min, base_max = base_range
        base_variation = random.randint(base_min, base_max)
        
        # Add more realistic variation patterns
        roll = random.random()
        if roll < 0.6:  # 60% chance for moderate variation
            variation_x = random.randint(-base_variation, base_variation)
            variation_y = random.randint(-base_variation, base_variation)
        elif roll < 0.9:  # 30% chance for more variation
            variation_x = random.randint(-base_variation-3, base_variation+3)
            variation_y = random.randint(-base_variation-3, base_variation+3)
        else:  # 10% chance for significant variation
            variation_x = random.randint(-base_variation-6, base_variation+6)
            variation_y = random.randint(-base_variation-6, base_variation+6)
        
        click_x = x + variation_x
        click_y = y + variation_y
        return (click_x, click_y)
    
    def human_click(self, position, action_name):
        """Click with human-like behavior"""
        try:
            # Increase variation specifically for darts to avoid repeat pixels
            varied_position = self.add_click_variation(position, base_range=(5, 12))
            x, y = varied_position
            
            # Get current mouse position
            current_x, current_y = pyautogui.position()
            
            # Calculate distance for movement speed
            distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
            
            # Natural human-like movement durations
            if distance < 50:
                movement_duration = random.uniform(0.08, 0.15)  # Quick but visible for small movements
            elif distance < 200:
                movement_duration = random.uniform(0.15, 0.3)   # Natural speed for medium movements
            else:
                movement_duration = random.uniform(0.25, 0.5)   # Slower for long movements
            
            # Human-like movement with slight curve
            # Add a small random offset for natural variation
            offset_x = random.randint(-3, 3)
            offset_y = random.randint(-3, 3)
            
            # Move to target with slight curve (more natural)
            # Add a waypoint for more human-like movement
            waypoint_x = current_x + (x - current_x) * random.uniform(0.3, 0.7)
            waypoint_y = current_y + (y - current_y) * random.uniform(0.3, 0.7)
            
            # Move through waypoint to target
            pyautogui.moveTo(waypoint_x + offset_x, waypoint_y + offset_y, duration=movement_duration * 0.6)
            pyautogui.moveTo(x, y, duration=movement_duration * 0.4)
            
            # Brief pause before clicking
            wait_time = random.uniform(0.02, 0.08)
            time.sleep(wait_time)
            
            pyautogui.click(x, y)
            
            if self.debug:
                print(f"   🖱️  {action_name} at ({x}, {y})")
            
            return True
        except Exception as e:
            print(f"Error clicking: {e}")
            return False

def test_dart_detection():
    """Continuously test dart icon detection on screen with clicking"""
    print("🎯 Testing Dart Detection with find_item method + Clicking")
    print("=" * 60)
    
    tester = DartTester()
    
    if not tester.dart_templates:
        print("❌ No dart templates found!")
        return
    
    print(f"\n📁 Testing {len(tester.dart_templates)} dart template(s)")
    print("⚠️  WARNING: This test will click on detected darts!")
    print("   Move mouse to corner to stop if needed.")
    print()
    
    while True:
        try:
            # Capture screen
            screenshot = pyautogui.screenshot()
            screen = np.array(screenshot)
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            print("\n🔍 Scanning for darts...")
            
            # Test individual templates
            print("\n📄 Testing individual templates:")
            for i, template in enumerate(tester.dart_templates):
                result, confidence = tester.find_template(screen, template, threshold=0.5)
                print(f"   Template {i+1}: {confidence:.3f}")
                if result:
                    print(f"      Found at: {result}")
            
            # Test the find_item method
            print("\n🎯 Testing find_item method:")
            dart_position, dart_confidence = tester.find_darts(screen)
            
            if dart_position and dart_confidence > 0.55:
                print(f"   ✅ Found darts at {dart_position} (confidence: {dart_confidence:.2f})")
                
                # Ask user if they want to click
                print("\n🤔 Click on detected darts? (y/n, or 'q' to quit)")
                user_input = input().lower().strip()
                
                if user_input == 'q':
                    print("🛑 Quitting test...")
                    break
                elif user_input == 'y':
                    print("   🖱️  Clicking on darts...")
                    if tester.human_click(dart_position, "🎯 Clicked darts"):
                        print("   ✅ Click successful!")
                        # Wait a moment to see the result
                        time.sleep(1)
                    else:
                        print("   ❌ Click failed!")
                else:
                    print("   ⏭️  Skipping click")
            else:
                print(f"   ❌ No darts found (best confidence: {dart_confidence:.2f})")
            
            print("\n" + "="*60)
            print("Press Ctrl+C to stop")
            time.sleep(2)  # Wait 2 seconds before next scan
            
        except KeyboardInterrupt:
            print("\n🛑 Stopping test...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    print("Starting Dart Detection Test with Clicking...")
    print("Make sure darts are visible on screen!")
    print("This test will ask if you want to click on detected darts.")
    print("Press Ctrl+C to stop")
    print()
    test_dart_detection()
