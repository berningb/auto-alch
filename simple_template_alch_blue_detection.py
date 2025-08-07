#!/usr/bin/env python3
"""
Version with blue outline detection for gemstone crab
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

class SimpleTemplateAlchBlueDetection:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.click_count = 0
        self.last_action_time = 0
        self.action_cooldown = random.uniform(0.1, 0.3)
        
        # State tracking
        self.waiting_for_alch_spell = True
        self.waiting_for_darts = False
        self.waiting_for_crab = False
        
        # Templates for recognition
        self.alch_spell_template = None
        self.dart_template = None
        
        # Remembered positions
        self.alch_spell_position = None
        self.dart_position = None
        self.crab_position = None
        
        # Position memory for fallback
        self.remembered_positions = {
            'alch_spell': [],
            'darts': [],
            'crab': []
        }
        
        # Click variation settings
        self.click_variation = random.randint(3, 8)
        
        # Position memory file
        self.position_file = "alch_positions.json"
        
        # Anti-detection settings
        self.session_start_time = time.time()
        self.last_break_time = time.time()
        self.break_interval = random.randint(600, 1200)
        self.break_duration = random.randint(30, 120)
        
        # Crab detection settings
        self.crab_fail_count = 0
        self.max_crab_fails = 5
        
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
            
            if os.path.exists("dart_template.png"):
                self.dart_template = cv2.imread("dart_template.png")
                print("   📂 Loaded dart template")
            elif os.path.exists("dart.png"):
                self.dart_template = cv2.imread("dart.png")
                print("   📂 Loaded dart template (fallback)")
            
            return self.alch_spell_template is not None and self.dart_template is not None
        except Exception as e:
            print(f"Error loading templates: {e}")
            return False
    
    def save_position(self, position_type, position):
        """Save a successful position for fallback use"""
        if position and position not in self.remembered_positions[position_type]:
            self.remembered_positions[position_type].append(position)
            # Keep only the last 5 positions for each type
            if len(self.remembered_positions[position_type]) > 5:
                self.remembered_positions[position_type].pop(0)
            print(f"   💾 Saved {position_type} position: {position}")
    
    def get_fallback_position(self, position_type):
        """Get a remembered position for fallback"""
        if self.remembered_positions[position_type]:
            return self.remembered_positions[position_type][-1]  # Return most recent
        return None
    
    def load_positions(self):
        """Load saved positions from file"""
        try:
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    data = json.load(f)
                    self.remembered_positions = data.get('remembered_positions', {
                        'alch_spell': [],
                        'darts': [],
                        'crab': []
                    })
                    print(f"   📂 Loaded {len(self.remembered_positions['alch_spell'])} alch spell positions")
                    print(f"   📂 Loaded {len(self.remembered_positions['darts'])} dart positions")
                    print(f"   📂 Loaded {len(self.remembered_positions['crab'])} crab positions")
        except Exception as e:
            print(f"Error loading positions: {e}")
    
    def save_positions(self):
        """Save positions to file"""
        try:
            data = {
                'remembered_positions': self.remembered_positions
            }
            with open(self.position_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"   💾 Saved positions to {self.position_file}")
        except Exception as e:
            print(f"Error saving positions: {e}")
    
    def find_template_in_screen(self, screen, template, threshold=0.7):
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
                
                # Check if the detected position is within reasonable screen bounds
                screen_height, screen_width = screen.shape[:2]
                if center_x < 0 or center_x > screen_width or center_y < 0 or center_y > screen_height:
                    print(f"   ⚠️ WARNING: Detected position ({center_x}, {center_y}) is outside screen bounds ({screen_width}x{screen_height})")
                    return None, max_val
                
                return (center_x, center_y), max_val
            else:
                return None, max_val
                
        except Exception as e:
            print(f"Error in template matching: {e}")
            return None, 0
    
    def detect_alch_spell(self, screen):
        """Detect alchemy spell using template matching"""
        position, confidence = self.find_template_in_screen(screen, self.alch_spell_template, threshold=0.7)
        if position:
            print(f"   🔮 Alchemy spell detected at {position} (confidence: {confidence:.2f})")
            self.save_position('alch_spell', position)
        else:
            # Try fallback position
            fallback_position = self.get_fallback_position('alch_spell')
            if fallback_position:
                print(f"   🔮 Using fallback alchemy spell position: {fallback_position}")
                return fallback_position, 0.8
        return position, confidence
    
    def detect_darts(self, screen):
        """Detect darts using template matching with blue detection fallback"""
        try:
            # First try template matching
            position, confidence = self.find_template_in_screen(screen, self.dart_template, threshold=0.6)
            if position:
                print(f"   🎯 Darts detected via template at {position} (confidence: {confidence:.2f})")
                self.save_position('darts', position)
                return position, confidence
            
            # If template fails, try blue detection in vicinity of remembered position
            fallback_position = self.get_fallback_position('darts')
            if fallback_position:
                print(f"   🎯 Template failed, trying blue detection near remembered position: {fallback_position}")
                
                # Define search area around remembered position (50px radius)
                search_x, search_y = fallback_position
                search_area = screen[max(0, search_y-50):min(screen.shape[0], search_y+50), 
                                   max(0, search_x-50):min(screen.shape[1], search_x+50)]
                
                if search_area.size > 0:
                    # Convert to HSV for blue detection
                    hsv = cv2.cvtColor(search_area, cv2.COLOR_BGR2HSV)
                    
                    # Define blue color range for 0A01E0 (darker blue)
                    lower_blue = np.array([110, 100, 100])   # Dark blue range
                    upper_blue = np.array([135, 255, 255])   # Dark blue range
                    
                    # Create mask for blue pixels
                    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
                    
                    # Find contours in the blue mask
                    contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    # Look for contours that could be the dart outline
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        x, y, w, h = cv2.boundingRect(contour)
                        
                        # Filter for reasonable size (dart outline should be smaller than crab)
                        if area > 1000 and area < 20000:
                            aspect_ratio = w / h
                            if 0.3 < aspect_ratio < 3.0:
                                # Calculate center relative to search area
                                center_x = x + w // 2
                                center_y = y + h // 2
                                
                                # Convert back to screen coordinates
                                screen_x = max(0, search_x-50) + center_x
                                screen_y = max(0, search_y-50) + center_y
                                
                                print(f"   🎯 Blue dart outline detected at ({screen_x}, {screen_y}) - area: {area:.0f}")
                                position = (screen_x, screen_y)
                                self.save_position('darts', position)
                                return position, 0.85  # Good confidence for color detection
                
                # If blue detection also fails, use the remembered position
                print(f"   🎯 Using fallback dart position: {fallback_position}")
                return fallback_position, 0.7
            
            return None, 0.0
            
        except Exception as e:
            print(f"Error in dart detection: {e}")
            return None, 0.0
    
    def detect_blue_outline(self, screen):
        """Detect gemstone crab by looking for blue outline"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # Define blue color range for FF00FFFF (bright cyan/light blue)
            # Based on debug testing, this range works best for the gemstone crab outline
            lower_blue = np.array([80, 50, 50])   # Broad cyan range
            upper_blue = np.array([100, 255, 255]) # Broad cyan range
            
            # Create mask for blue pixels
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Find contours in the blue mask
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for contours that could be the crab outline
            for contour in contours:
                # Get contour area and bounding rectangle
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for reasonable size (crab outline should be large)
                if area > 50000 and area < 150000:  # Adjusted for the detected crab outline size
                    # Check aspect ratio (should be roughly square-ish)
                    aspect_ratio = w / h
                    if 0.5 < aspect_ratio < 2.0:
                        # Calculate center of the contour
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        # Check if position is within screen bounds
                        screen_height, screen_width = screen.shape[:2]
                        if 0 <= center_x < screen_width and 0 <= center_y < screen_height:
                            print(f"   🦀 Blue outline detected at ({center_x}, {center_y}) - area: {area:.0f}")
                            position = (center_x, center_y)
                            self.save_position('crab', position)
                            return position, 0.95  # Very high confidence for exact color match
            
            # If no suitable contour found
            print(f"   🦀 No blue outline detected")
            # Try fallback position
            fallback_position = self.get_fallback_position('crab')
            if fallback_position:
                print(f"   🦀 Using fallback crab position: {fallback_position}")
                return fallback_position, 0.8
            return None, 0.0
            
        except Exception as e:
            print(f"Error in blue outline detection: {e}")
            return None, 0.0
    
    def detect_crab(self, screen):
        """Detect gemstone crab using blue outline detection"""
        return self.detect_blue_outline(screen)
    
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
    
    def click_darts(self, position):
        """Click on the darts with human-like behavior"""
        try:
            if self.move_and_click(position, "🎯 Clicked darts", instant_click=False):
                self.click_count += 1
                print(f"   📊 Total clicks: {self.click_count}")
                return True
            return False
        except Exception as e:
            print(f"Error clicking darts: {e}")
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
        """Start the blue outline detection version"""
        print("🔍 Starting Blue Outline Detection Version")
        print("Step 1: Find alchemy spell")
        print("Step 2: Click spell")
        print("Step 3: Find darts")
        print("Step 4: Click darts")
        print("Step 5: Find gemstone crab (blue outline detection)")
        print("Step 6: Click crab")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        print("🔧 BLUE DETECTION: Detects crab by blue outline instead of template")
        
        # Load saved templates
        has_templates = self.load_templates()
        
        if not has_templates:
            print("❌ No saved templates found. Please run the script once to capture templates.")
            return
        
        print("✅ Using saved templates - no user input required")
        
        # Load saved positions
        self.load_positions()
        
        self.is_watching = True
        self.previous_screenshot = None
        self.last_action_time = time.time()
        self.last_save_time = time.time()
        
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
                            alch_position, alch_confidence = self.detect_alch_spell(current_frame)
                            
                            if alch_position and alch_confidence > 0.7:
                                print(f"   🔮 Alchemy spell found (confidence: {alch_confidence:.2f})")
                                self.alch_spell_position = alch_position
                                if self.click_alch_spell(alch_position):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for darts...")
                        
                        elif self.waiting_for_darts:
                            dart_position, dart_confidence = self.detect_darts(current_frame)
                            
                            if dart_position and dart_confidence > 0.6:
                                print(f"   🎯 Darts found (confidence: {dart_confidence:.2f})")
                                self.dart_position = dart_position
                                if self.click_darts(dart_position):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_darts = False
                                    self.waiting_for_crab = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for gemstone crab...")
                        
                        elif self.waiting_for_crab:
                            crab_position, crab_confidence = self.detect_crab(current_frame)
                            
                            if crab_position:
                                print(f"   🦀 Gemstone Crab found (confidence: {crab_confidence:.2f})")
                                self.crab_position = crab_position
                                if self.click_crab(crab_position):
                                    self.waiting_for_alch_spell = True
                                    self.waiting_for_darts = False
                                    self.waiting_for_crab = False
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for alchemy spell...")
                            else:
                                # If crab detection fails too many times, skip it
                                if self.crab_fail_count >= self.max_crab_fails:
                                    print(f"   ⚠️ Crab detection failing repeatedly. Skipping crab...")
                                    self.waiting_for_alch_spell = True
                                    self.waiting_for_darts = False
                                    self.waiting_for_crab = False
                                    self.crab_fail_count = 0  # Reset counter
                                    self.last_action_time = current_time
                                    print("   🔄 Skipping crab, returning to alchemy spell...")
                                else:
                                    self.crab_fail_count += 1
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                    
                    # Save positions periodically (every 30 seconds)
                    if current_time - self.last_save_time > 30:
                        self.save_positions()
                        self.last_save_time = current_time
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Blue Outline Detection...")
                print(f"📊 Total clicks performed: {self.click_count}")
                self.save_positions()  # Save positions before stopping
                self.is_watching = False
                break
            except Exception as e:
                print(f"Error in watching loop: {e}")
                time.sleep(1)
    
    def stop_watching(self):
        """Stop the screen watching process"""
        self.is_watching = False

def main():
    """Main function to run the Blue Outline Detection Alch Clicker"""
    print("🤖 Blue Outline Detection - Advanced Anti-Detection Alch Clicker")
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
    
    # Create and start the Blue Outline Detection Alch Clicker
    clicker = SimpleTemplateAlchBlueDetection()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
