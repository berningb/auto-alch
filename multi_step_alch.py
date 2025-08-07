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

class MultiStepAlch:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.click_count = 0
        self.last_action_time = 0
        self.action_cooldown = 0.5  # Minimum time between actions
        
        # State tracking
        self.waiting_for_alch_spell = True
        self.waiting_for_arrows = False
        
        # Templates for recognition
        self.alch_spell_template = None
        self.arrow_template = None
        
        # Remembered positions
        self.alch_spell_position = None
        self.arrow_position = None
        
        # Click variation settings
        self.click_variation = 15  # Pixels to vary from center
        
        # Position memory file
        self.position_file = "alch_positions.json"
        
    def capture_screen(self):
        """Capture the current screen"""
        try:
            screenshot = pyautogui.screenshot()
            # Convert to numpy array for OpenCV processing
            frame = np.array(screenshot)
            # Convert from RGB to BGR (OpenCV format)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def create_alch_spell_template(self):
        """Create template for alchemy spell (coins + potion bottle)"""
        try:
            # Create a template based on the alchemy spell characteristics
            # We'll look for the distinctive pattern: coins + potion bottle
            template = np.zeros((30, 30, 3), dtype=np.uint8)
            
            # Add some basic pattern recognition for the alchemy spell
            # This is a simplified template - in practice, you'd capture the actual spell
            # For now, we'll use template matching with a captured image
            
            # Save template for later use
            cv2.imwrite("alch_spell_template.png", template)
            return template
        except Exception as e:
            print(f"Error creating alch spell template: {e}")
            return None
    
    def create_arrow_template(self):
        """Create template for arrows (with number above)"""
        try:
            # Create a template based on the arrows characteristics
            # We'll look for the distinctive pattern: arrows with number above
            template = np.zeros((40, 40, 3), dtype=np.uint8)
            
            # Add some basic pattern recognition for the arrows
            # This is a simplified template - in practice, you'd capture the actual arrows
            
            # Save template for later use
            cv2.imwrite("arrow_template.png", template)
            return template
        except Exception as e:
            print(f"Error creating arrow template: {e}")
            return None
    
    def find_template_in_screen(self, screen, template, threshold=0.8):
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
        """Detect alchemy spell using color and pattern detection"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # Look for gold/yellow colors (coins)
            lower_gold = np.array([15, 100, 100])
            upper_gold = np.array([30, 255, 255])
            
            # Look for blue colors (potion bottle)
            lower_blue = np.array([100, 100, 100])
            upper_blue = np.array([130, 255, 255])
            
            # Create masks
            gold_mask = cv2.inRange(hsv, lower_gold, upper_gold)
            blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
            
            # Combine masks
            combined_mask = cv2.bitwise_or(gold_mask, blue_mask)
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for small regions that could be the alchemy spell
            alch_candidates = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for reasonable alchemy spell dimensions
                if 20 <= w <= 60 and 20 <= h <= 60:
                    area = w * h
                    if 400 <= area <= 3600:  # Reasonable area for spell icon
                        alch_candidates.append((x, y, w, h, area))
            
            # Sort by area (largest first)
            alch_candidates.sort(key=lambda x: x[4], reverse=True)
            
            if alch_candidates:
                x, y, w, h, area = alch_candidates[0]
                center_x = x + w // 2
                center_y = y + h // 2
                
                print(f"   🔮 Alchemy spell detected at ({center_x}, {center_y}) - size: {w}x{h}")
                return (center_x, center_y), 0.8
            else:
                return None, 0
                
        except Exception as e:
            print(f"Error detecting alchemy spell: {e}")
            return None, 0
    
    def detect_arrows(self, screen):
        """Detect arrows using color and pattern detection"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # Look for black/dark colors (arrow shafts)
            lower_black = np.array([0, 0, 0])
            upper_black = np.array([180, 255, 50])
            
            # Look for green colors (arrow fletching)
            lower_green = np.array([35, 50, 50])
            upper_green = np.array([85, 255, 255])
            
            # Look for yellow/orange colors (arrowheads)
            lower_yellow = np.array([15, 100, 100])
            upper_yellow = np.array([35, 255, 255])
            
            # Create masks
            black_mask = cv2.inRange(hsv, lower_black, upper_black)
            green_mask = cv2.inRange(hsv, lower_green, upper_green)
            yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            # Combine masks
            combined_mask = cv2.bitwise_or(cv2.bitwise_or(black_mask, green_mask), yellow_mask)
            
            # Find contours
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for regions that could be arrows
            arrow_candidates = []
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter for reasonable arrow dimensions
                if 30 <= w <= 120 and 20 <= h <= 60:
                    area = w * h
                    if 600 <= area <= 7200:  # Reasonable area for arrows
                        arrow_candidates.append((x, y, w, h, area))
            
            # Sort by area (largest first)
            arrow_candidates.sort(key=lambda x: x[4], reverse=True)
            
            if arrow_candidates:
                x, y, w, h, area = arrow_candidates[0]
                center_x = x + w // 2
                center_y = y + h // 2
                
                print(f"   🏹 Arrows detected at ({center_x}, {center_y}) - size: {w}x{h}")
                return (center_x, center_y), 0.8
            else:
                return None, 0
                
        except Exception as e:
            print(f"Error detecting arrows: {e}")
            return None, 0
    
    def add_click_variation(self, position):
        """Add random variation to click position"""
        x, y = position
        
        # Add random variation within the click_variation range
        variation_x = random.randint(-self.click_variation, self.click_variation)
        variation_y = random.randint(-self.click_variation, self.click_variation)
        
        new_x = x + variation_x
        new_y = y + variation_y
        
        return (new_x, new_y)
    
    def move_and_click(self, position, action_name, instant_click=False):
        """Move mouse to position and click with human-like behavior"""
        try:
            # Add random variation to click position
            varied_position = self.add_click_variation(position)
            x, y = varied_position
            
            # Move mouse to the position
            pyautogui.moveTo(x, y, duration=random.uniform(0.8, 1.2))
            
            # Wait time depends on whether it's instant or not
            if instant_click:
                wait_time = 0.1  # Almost instant for alch spell
                print(f"   ⚡ Instant click (no wait)...")
            else:
                wait_time = random.uniform(1.0, 3.0)  # Normal wait for arrows
                print(f"   ⏳ Waiting {wait_time:.1f}s before clicking...")
            
            time.sleep(wait_time)
            
            # Click
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
    
    def save_positions(self):
        """Save remembered positions to file"""
        try:
            positions = {
                "alch_spell_position": self.alch_spell_position,
                "arrow_position": self.arrow_position,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.position_file, 'w') as f:
                json.dump(positions, f, indent=2)
            
            print(f"   💾 Positions saved to {self.position_file}")
        except Exception as e:
            print(f"Error saving positions: {e}")
    
    def load_positions(self):
        """Load remembered positions from file"""
        try:
            if os.path.exists(self.position_file):
                with open(self.position_file, 'r') as f:
                    positions = json.load(f)
                
                self.alch_spell_position = positions.get("alch_spell_position")
                self.arrow_position = positions.get("arrow_position")
                
                print(f"   📂 Loaded positions from {self.position_file}")
                if self.alch_spell_position:
                    print(f"   🔮 Alchemy spell position: {self.alch_spell_position}")
                if self.arrow_position:
                    print(f"   🏹 Arrow position: {self.arrow_position}")
                
                return True
            else:
                print(f"   📂 No saved positions found, will learn new positions")
                return False
        except Exception as e:
            print(f"Error loading positions: {e}")
            return False
    
    def detect_change(self, current_frame, previous_frame, threshold=0.1):
        """Detect if there's a significant change between frames"""
        if previous_frame is None:
            return True
        
        try:
            # Convert to grayscale for comparison
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            previous_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate difference
            diff = cv2.absdiff(current_gray, previous_gray)
            
            # Calculate percentage of changed pixels
            total_pixels = diff.shape[0] * diff.shape[1]
            changed_pixels = np.count_nonzero(diff > 30)
            change_percentage = changed_pixels / total_pixels
            
            return change_percentage > threshold
            
        except Exception as e:
            print(f"Error detecting change: {e}")
            return False
    
    def start_watching(self):
        """Start the multi-step alch clicking process"""
        print("🔍 Starting Multi-Step Alch Clicker...")
        print("Step 1: Find alchemy spell")
        print("Step 2: Click spell")
        print("Step 3: Find arrows")
        print("Step 4: Click arrows")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        
        # Try to load saved positions first
        has_saved_positions = self.load_positions()
        
        self.is_watching = True
        self.previous_screenshot = None
        self.last_action_time = time.time()
        
        while self.is_watching:
            try:
                current_time = time.time()
                
                # Capture current screen
                current_frame = self.capture_screen()
                
                if current_frame is not None:
                    # Check for changes
                    has_changed = self.detect_change(current_frame, self.previous_screenshot)
                    
                    # Only act if enough time has passed since last action
                    if current_time - self.last_action_time >= self.action_cooldown:
                        
                        if self.waiting_for_alch_spell:
                            # Step 1: Look for alchemy spell
                            if self.alch_spell_position and has_saved_positions:
                                # Use remembered position
                                print(f"   🔮 Using remembered alchemy spell position: {self.alch_spell_position}")
                                if self.click_alch_spell(self.alch_spell_position):
                                    self.waiting_for_alch_spell = False
                                    self.waiting_for_arrows = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for arrows...")
                            else:
                                # Find alchemy spell
                                alch_position, alch_confidence = self.detect_alch_spell(current_frame)
                                
                                if alch_position and alch_confidence > 0.7:
                                    print(f"   🔮 Alchemy spell found (confidence: {alch_confidence:.2f})")
                                    self.alch_spell_position = alch_position
                                    if self.click_alch_spell(alch_position):
                                        self.waiting_for_alch_spell = False
                                        self.waiting_for_arrows = True
                                        self.last_action_time = current_time
                                        print("   🔄 Now waiting for arrows...")
                        
                        elif self.waiting_for_arrows:
                            # Step 3: Look for arrows
                            if self.arrow_position and has_saved_positions:
                                # Use remembered position
                                print(f"   🏹 Using remembered arrow position: {self.arrow_position}")
                                if self.click_arrows(self.arrow_position):
                                    self.waiting_for_alch_spell = True
                                    self.waiting_for_arrows = False
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for alchemy spell...")
                            else:
                                # Find arrows
                                arrow_position, arrow_confidence = self.detect_arrows(current_frame)
                                
                                if arrow_position and arrow_confidence > 0.7:
                                    print(f"   🏹 Arrows found (confidence: {arrow_confidence:.2f})")
                                    self.arrow_position = arrow_position
                                    if self.click_arrows(arrow_position):
                                        self.waiting_for_alch_spell = True
                                        self.waiting_for_arrows = False
                                        self.last_action_time = current_time
                                        print("   🔄 Now waiting for alchemy spell...")
                                        
                                        # Save positions after successful cycle
                                        self.save_positions()
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)  # Faster response time for template matching
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Multi-Step Alch Clicker...")
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
    """Main function to run the Multi-Step Alch Clicker"""
    print("🤖 Multi-Step Alch Clicker - Smart Detection")
    print("=" * 55)
    
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
    
    # Create and start the Multi-Step Alch Clicker
    clicker = MultiStepAlch()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
