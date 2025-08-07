#!/usr/bin/env python3
"""
Debug version of simple template alch with lower thresholds and verbose output
"""

import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
import random
import os
import json

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 0.1  # Small pause between actions

class SimpleTemplateAlchDebug:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.click_count = 0
        self.last_action_time = 0
        self.action_cooldown = random.uniform(0.1, 0.3)
        
        # State tracking
        self.waiting_for_alch_spell = True
        self.waiting_for_arrows = False
        self.waiting_for_crab = False
        
        # Templates for recognition
        self.alch_spell_template = None
        self.arrow_template = None
        self.crab_template = None
        
        # Remembered positions
        self.alch_spell_position = None
        self.arrow_position = None
        self.crab_position = None
        
        # Click variation settings
        self.click_variation = random.randint(3, 8)
        
        # Position memory file
        self.position_file = "alch_positions.json"
        
        # Anti-detection settings
        self.session_start_time = time.time()
        self.last_break_time = time.time()
        self.break_interval = random.randint(600, 1200)
        self.break_duration = random.randint(30, 120)
        
    def capture_screen(self):
        """Capture the current screen"""
        try:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def load_templates(self):
        """Load saved templates if they exist"""
        try:
            if os.path.exists("alch_spell_template.png"):
                self.alch_spell_template = cv2.imread("alch_spell_template.png")
                print("   📂 Loaded alchemy spell template")
            
            if os.path.exists("arrow_template.png"):
                self.arrow_template = cv2.imread("arrow_template.png")
                print("   📂 Loaded arrow template")
            
            if os.path.exists("crab_template.png"):
                self.crab_template = cv2.imread("crab_template.png")
                print("   📂 Loaded gemstone crab template")
            
            return self.alch_spell_template is not None and self.arrow_template is not None and self.crab_template is not None
        except Exception as e:
            print(f"Error loading templates: {e}")
            return False
    
    def find_template_in_screen(self, screen, template, threshold=0.5):  # Lower threshold for debugging
        """Find template in screen using template matching"""
        try:
            if template is None:
                return None, 0
            
            # Convert to grayscale for template matching
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Perform template matching
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Return center of matched region
                h, w = template_gray.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y), max_val
            else:
                return None, max_val
                
        except Exception as e:
            print(f"Error in template matching: {e}")
            return None, 0
    
    def detect_alch_spell(self, screen):
        """Detect alchemy spell using template matching"""
        position, confidence = self.find_template_in_screen(screen, self.alch_spell_template, threshold=0.5)
        if position:
            print(f"   🔮 Alchemy spell detected at {position} (confidence: {confidence:.2f})")
        return position, confidence
    
    def detect_arrows(self, screen):
        """Detect arrows using template matching"""
        position, confidence = self.find_template_in_screen(screen, self.arrow_template, threshold=0.5)
        if position:
            print(f"   🏹 Arrows detected at {position} (confidence: {confidence:.2f})")
        return position, confidence
    
    def detect_crab(self, screen):
        """Detect gemstone crab using template matching"""
        position, confidence = self.find_template_in_screen(screen, self.crab_template, threshold=0.5)
        if position:
            print(f"   🦀 Gemstone Crab detected at {position} (confidence: {confidence:.2f})")
        else:
            print(f"   🦀 Crab NOT detected (best confidence: {confidence:.2f})")
        return position, confidence
    
    def add_click_variation(self, position):
        """Add random variation to click position"""
        x, y = position
        current_variation = random.randint(2, 6)
        variation_x = random.randint(-current_variation, current_variation)
        variation_y = random.randint(-current_variation, current_variation)
        
        if random.random() < 0.02:
            variation_x += random.randint(-2, 2)
            variation_y += random.randint(-2, 2)
        
        new_x = x + variation_x
        new_y = y + variation_y
        return (new_x, new_y)
    
    def move_and_click(self, position, action_name, instant_click=False):
        """Move mouse to position and click with human-like behavior"""
        try:
            varied_position = self.add_click_variation(position)
            x, y = varied_position
            
            movement_duration = random.uniform(0.2, 0.8)
            pyautogui.moveTo(x, y, duration=movement_duration)
            
            if instant_click:
                wait_time = random.uniform(0.02, 0.15)
                print(f"   ⚡ Quick click (wait: {wait_time:.2f}s)...")
            else:
                wait_time = random.uniform(0.3, 1.5)
                print(f"   ⏳ Waiting {wait_time:.1f}s before clicking...")
            
            time.sleep(wait_time)
            pyautogui.click(x, y)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {action_name} at ({x}, {y}) [varied from center]")
            
            return True
        except Exception as e:
            print(f"Error in move_and_click: {e}")
            return False
    
    def click_alch_spell(self, position):
        """Click on the alch spell with instant behavior"""
        return self.move_and_click(position, "🔮 Clicked alchemy spell", instant_click=True)
    
    def click_arrows(self, position):
        """Click on the arrows with human-like behavior"""
        try:
            if self.move_and_click(position, "🏹 Clicked arrows", instant_click=False):
                self.click_count += 1
                print(f"   📊 Total clicks: {self.click_count}")
                return True
            return False
        except Exception as e:
            print(f"Error clicking arrows: {e}")
            return False
    
    def click_crab(self, position):
        """Click on the gemstone crab with human-like behavior"""
        try:
            if self.move_and_click(position, "🦀 Clicked gemstone crab", instant_click=False):
                return True
            return False
        except Exception as e:
            print(f"Error clicking crab: {e}")
            return False
    
    def start_watching(self):
        """Start the debug version of the alch clicking process"""
        print("🔍 Starting Debug Version - Advanced Anti-Detection Alch Clicker...")
        print("Step 1: Find alchemy spell")
        print("Step 2: Click spell")
        print("Step 3: Find arrows")
        print("Step 4: Click arrows")
        print("Step 5: Find gemstone crab")
        print("Step 6: Click crab")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        print("🔧 DEBUG MODE: Lower thresholds and verbose output")
        
        # Load saved templates
        has_templates = self.load_templates()
        
        if not has_templates:
            print("❌ No saved templates found. Please run the script once to capture templates.")
            return
        
        print("✅ Using saved templates - no user input required")
        
        # Don't use saved positions, always find images on screen
        has_saved_positions = False
        
        self.is_watching = True
        self.previous_screenshot = None
        self.last_action_time = time.time()
        
        while self.is_watching:
            try:
                current_time = time.time()
                
                # Capture current screen
                current_frame = self.capture_screen()
                
                if current_frame is not None:
                    # Only act if enough time has passed since last action
                    current_cooldown = random.uniform(0.1, 0.5)
                    if current_time - self.last_action_time >= current_cooldown:
                        
                        if self.waiting_for_alch_spell:
                            print("   🔍 Looking for alchemy spell...")
                            alch_position, alch_confidence = self.detect_alch_spell(current_frame)
                            
                            if alch_position and alch_confidence > 0.5:  # Lower threshold
                                print(f"   🔮 Alchemy spell found (confidence: {alch_confidence:.2f})")
                                self.alch_spell_position = alch_position
                                if self.click_alch_spell(alch_position):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_arrows = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for arrows...")
                            else:
                                print(f"   ⚠️ Alchemy spell not found (best confidence: {alch_confidence:.2f})")
                        
                        elif self.waiting_for_arrows:
                            print("   🔍 Looking for arrows...")
                            arrow_position, arrow_confidence = self.detect_arrows(current_frame)
                            
                            if arrow_position and arrow_confidence > 0.5:  # Lower threshold
                                print(f"   🏹 Arrows found (confidence: {arrow_confidence:.2f})")
                                self.arrow_position = arrow_position
                                if self.click_arrows(arrow_position):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_arrows = False
                                    self.waiting_for_crab = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for gemstone crab...")
                            else:
                                print(f"   ⚠️ Arrows not found (best confidence: {arrow_confidence:.2f})")
                        
                        elif self.waiting_for_crab:
                            print("   🔍 Looking for gemstone crab...")
                            crab_position, crab_confidence = self.detect_crab(current_frame)
                            
                            if crab_position and crab_confidence > 0.5:  # Lower threshold
                                print(f"   🦀 Gemstone Crab found (confidence: {crab_confidence:.2f})")
                                self.crab_position = crab_position
                                if self.click_crab(crab_position):
                                    self.waiting_for_alch_spell = True
                                    self.waiting_for_arrows = False
                                    self.waiting_for_crab = False
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for alchemy spell...")
                            else:
                                print(f"   ⚠️ Crab not found (best confidence: {crab_confidence:.2f})")
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Debug Alch Clicker...")
                print(f"📊 Total clicks performed: {self.click_count}")
                self.is_watching = False
                break
            except Exception as e:
                print(f"Error in watching loop: {e}")
                time.sleep(1)
    
    def stop_watching(self):
        """Stop the screen watching process"""
        self.is_watching = False

def main():
    """Main function to run the Debug Alch Clicker"""
    print("🤖 Debug Version - Advanced Anti-Detection Alch Clicker")
    print("=" * 60)
    
    # Check if required packages are available
    try:
        import cv2
        import pyautogui
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install required packages:")
        print("python -m pip install opencv-python pyautogui numpy")
        return
    
    # Create and start the Debug Alch Clicker
    clicker = SimpleTemplateAlchDebug()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
