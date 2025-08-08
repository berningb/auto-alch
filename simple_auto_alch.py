#!/usr/bin/env python3
"""
Simple Auto Alch - Clicks alch spell then darts
"""

import cv2
import numpy as np
import pyautogui
import time
import random
import os
from datetime import datetime

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 0.1  # Small pause between actions

class SimpleAutoAlch:
    def __init__(self):
        self.alch_spell_template = None
        self.dart_template = None
        self.click_count = 0
        self.is_running = False
        
        # Humanization settings
        self.session_start_time = time.time()
        self.last_break_time = time.time()
        self.break_interval = random.randint(600, 1200)  # 10-20 minutes
        self.break_duration = random.randint(30, 120)  # 30 seconds - 2 minutes
        
        # State tracking
        self.waiting_for_alch_spell = True
        self.waiting_for_darts = False
        
    def load_templates(self):
        """Load the template images"""
        try:
            # Load alch spell templates
            self.alch_spell_template = None
            self.alch_spell_template2 = None
            
            # Get absolute paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            alch_path = os.path.join(current_dir, "alc-spell.png")
            alch2_path = os.path.join(current_dir, "alc-spell2.png")
            
            print(f"Looking for alch templates in: {current_dir}")
            print(f"Full path 1: {alch_path}")
            print(f"Full path 2: {alch2_path}")
            
            if os.path.exists(alch_path):
                self.alch_spell_template = cv2.imread(alch_path)
                print("✅ Loaded alch spell template 1 (alc-spell.png)")
            else:
                print(f"❌ Could not find {alch_path}")
            
            if os.path.exists(alch2_path):
                self.alch_spell_template2 = cv2.imread(alch2_path)
                print("✅ Loaded alch spell template 2 (alc-spell2.png)")
            else:
                print(f"❌ Could not find {alch2_path}")
            
            if self.alch_spell_template is None and self.alch_spell_template2 is None:
                print("❌ No alch spell templates found. Please create alc-spell.png or alc-spell2.png")
                return False
            
            # Load dart templates
            self.dart_template = None
            self.dart_template2 = None
            
            dart_path = os.path.join(current_dir, "dart.png")
            if os.path.exists(dart_path):
                self.dart_template = cv2.imread(dart_path)
                print("✅ Loaded dart template 1 (dart.png)")
            else:
                print(f"❌ Could not find {dart_path}")
            
            dart2_path = os.path.join(current_dir, "dart2.png")
            if os.path.exists(dart2_path):
                self.dart_template2 = cv2.imread(dart2_path)
                print("✅ Loaded dart template 2 (dart2.png)")
            else:
                print(f"❌ Could not find {dart2_path}")
            
            if self.dart_template is None and self.dart_template2 is None:
                print("❌ No dart templates found. Please create dart.png or dart2.png")
                return False
                
            return True
        except Exception as e:
            print(f"Error loading templates: {e}")
            return False
    
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
    
    def find_alch_spell(self, screen):
        """Find alch spell in screen using both templates"""
        # Try both alch spell templates and use the one with better confidence
        result1, conf1 = self.find_template(screen, self.alch_spell_template, threshold=0.6)
        result2, conf2 = self.find_template(screen, self.alch_spell_template2, threshold=0.6)
        
        # Use whichever template gives better confidence
        if conf1 > conf2:
            print(f"   📊 Using alch template 1 (confidence: {conf1:.2f})")
            return result1, conf1
        else:
            print(f"   📊 Using alch template 2 (confidence: {conf2:.2f})")
            return result2, conf2
    
    def find_darts(self, screen):
        """Find darts in screen"""
        # Try both dart templates and use the one with better confidence
        result1, conf1 = self.find_template(screen, self.dart_template, threshold=0.55)
        result2, conf2 = self.find_template(screen, self.dart_template2, threshold=0.55)
        
        # Use whichever template gives better confidence
        if conf1 > conf2:
            print(f"   📊 Using dart template 1 (confidence: {conf1:.2f})")
            return result1, conf1
        else:
            print(f"   📊 Using dart template 2 (confidence: {conf2:.2f})")
            return result2, conf2
    
    def add_click_variation(self, position):
        """Add random variation to click position"""
        x, y = position
        
        # Much more natural variation - humans don't click the exact same spot
        base_variation = random.randint(3, 8)  # Increased variation
        
        # Add more realistic variation patterns
        if random.random() < 0.6:  # 60% chance for moderate variation
            variation_x = random.randint(-base_variation, base_variation)
            variation_y = random.randint(-base_variation, base_variation)
        elif random.random() < 0.3:  # 30% chance for more variation
            variation_x = random.randint(-base_variation-2, base_variation+2)
            variation_y = random.randint(-base_variation-2, base_variation+2)
        else:  # 10% chance for significant variation
            variation_x = random.randint(-base_variation-4, base_variation+4)
            variation_y = random.randint(-base_variation-4, base_variation+4)
        
        click_x = x + variation_x
        click_y = y + variation_y
        return (click_x, click_y)
    
    def human_click(self, position, action_name):
        """Click with human-like behavior"""
        try:
            varied_position = self.add_click_variation(position)
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
            
            # Brief pause before clicking (much shorter)
            wait_time = random.uniform(0.02, 0.08)
            time.sleep(wait_time)
            
            pyautogui.click(x, y)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {action_name} at ({x}, {y})")
            
            return True
        except Exception as e:
            print(f"Error clicking: {e}")
            return False
    
    def press_key(self, key):
        """Press a key with human-like timing"""
        try:
            print(f"   ⌨️ Pressing '{key}' to open spellbook...")
            time.sleep(random.uniform(0.1, 0.3))
            pyautogui.press(key)
            time.sleep(random.uniform(0.2, 0.5))
            return True
        except Exception as e:
            print(f"Error pressing key '{key}': {e}")
            return False
    
    def check_break_time(self):
        """Check if it's time for a break"""
        current_time = time.time()
        session_time = current_time - self.session_start_time
        time_since_last_break = current_time - self.last_break_time
        
        if time_since_last_break >= self.break_interval:
            print(f"   ☕ Break time! Taking a {self.break_duration} second break...")
            print(f"   📊 Session stats: {self.click_count} clicks in {session_time/60:.1f} minutes")
            time.sleep(self.break_duration)
            self.last_break_time = current_time
            self.break_interval = random.randint(600, 1200)  # New random interval
            print("   ✅ Break finished, resuming...")
            return True
        return False
    
    def capture_screen(self):
        """Capture current screen"""
        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def start(self):
        """Start the auto alch process"""
        print("🤖 Simple Auto Alch - Alch Spell + Darts")
        print("=" * 50)
        print("Steps:")
        print("1. Find and click alch spell")
        print("2. Find and click darts")
        print("3. Repeat")
        print()
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner for emergency stop.")
        print(f"⏰ Break every {self.break_interval/60:.1f} minutes")
        print()
        
        # Load templates
        if not self.load_templates():
            return
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Check for break time
                self.check_break_time()
                
                # Capture screen
                screen = self.capture_screen()
                if screen is None:
                    continue
                
                if self.waiting_for_alch_spell:
                    print("   🔍 Looking for alch spell...")
                    
                    # First try to find alch spell without pressing '3'
                    alch_position, alch_confidence = self.find_alch_spell(screen)
                    
                    if alch_position and alch_confidence > 0.7:
                        print(f"   🔮 Found alch spell (confidence: {alch_confidence:.2f})")
                        if self.human_click(alch_position, "🔮 Clicked alch spell"):
                            self.waiting_for_alch_spell = False
                            self.waiting_for_darts = True
                            print("   🔄 Now looking for darts...")
                            print("   ⏳ Waiting for alch spell animation...")
                            time.sleep(random.uniform(3.0, 4.0))  # Wait for alch spell animation
                    else:
                        # Only press '3' if we can't find the alch spell
                        print("   🔍 Alch spell not found, pressing '3' to open spellbook...")
                        self.press_key('3')
                        time.sleep(0.5)
                        
                        # Check again after pressing '3'
                        screen = self.capture_screen()
                        if screen is not None:
                            alch_position, alch_confidence = self.find_alch_spell(screen)
                            if alch_position and alch_confidence > 0.7:
                                print(f"   🔮 Found alch spell (confidence: {alch_confidence:.2f})")
                                if self.human_click(alch_position, "🔮 Clicked alch spell"):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = True
                                    print("   🔄 Now looking for darts...")
                                    print("   ⏳ Waiting for alch spell animation...")
                                    time.sleep(random.uniform(3.0, 4.0))  # Wait for alch spell animation
                            else:
                                print("   🔍 Alch spell still not found, retrying...")
                                time.sleep(0.5)
                        
                        # Capture new frame after pressing key
                        updated_screen = self.capture_screen()
                        if updated_screen is not None:
                            alch_position, alch_confidence = self.find_alch_spell(updated_screen)
                            
                            if alch_position and alch_confidence > 0.7:
                                print(f"   🔮 Found alch spell (confidence: {alch_confidence:.2f})")
                                if self.human_click(alch_position, "🔮 Clicked alch spell"):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = True
                                    print("   🔄 Now looking for darts...")
                                    print("   ⏳ Waiting 3-4 seconds for alch spell animation...")
                                    time.sleep(random.uniform(3.0, 4.0))  # Wait for alch spell animation
                            else:
                                print("   🔍 Alch spell still not found, retrying...")
                                time.sleep(0.5)
                
                elif self.waiting_for_darts:
                    print("   🔍 Looking for darts...")
                    dart_position, dart_confidence = self.find_darts(screen)
                    
                    if dart_position and dart_confidence > 0.55:
                        print(f"   🎯 Found darts (confidence: {dart_confidence:.2f})")
                        if self.human_click(dart_position, "🎯 Clicked darts"):
                            self.click_count += 1
                            print(f"   📊 Total clicks: {self.click_count}")
                            self.waiting_for_alch_spell = True
                            self.waiting_for_darts = False
                            print("   🔄 Now looking for alch spell...")
                            time.sleep(random.uniform(0.5, 1.0))
                    else:
                        print(f"   🔍 Darts not found (best match: {dart_confidence:.2f}), retrying...")
                        time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Auto Alch...")
                session_time = time.time() - self.session_start_time
                print(f"📊 Session stats:")
                print(f"   - Total clicks: {self.click_count}")
                print(f"   - Session time: {session_time/60:.1f} minutes")
                print(f"   - Clicks per minute: {self.click_count/(session_time/60):.1f}")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

def main():
    """Main function"""
    print("Starting Simple Auto Alch...")
    
    # Check imports
    try:
        import cv2
        import pyautogui
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Install with: pip install opencv-python pyautogui numpy")
        return
    
    # Create and start
    alch = SimpleAutoAlch()
    alch.start()

if __name__ == "__main__":
    main()
