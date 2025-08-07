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

class SimpleTemplateAlch:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.click_count = 0
        self.last_action_time = 0
        self.action_cooldown = random.uniform(0.1, 0.3)  # Much faster, more realistic
        
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
        self.click_variation = random.randint(3, 8)  # Much smaller, realistic variation
        
        # Position memory file
        self.position_file = "alch_positions.json"
        
        # Anti-detection settings
        self.session_start_time = time.time()
        self.last_break_time = time.time()
        self.break_interval = random.randint(600, 1200)  # 10-20 minutes between breaks
        self.break_duration = random.randint(30, 120)  # 30 seconds to 2 minutes
        
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
    
    def capture_alch_spell_template(self):
        """Capture the alchemy spell template by user positioning"""
        print("🔮 Please move your mouse over the Alchemy spell icon (coins + potion) and press Enter...")
        input("Press Enter when mouse is over the Alchemy spell...")
        
        x, y = pyautogui.position()
        
        # Capture a region around the mouse position
        try:
            screenshot = pyautogui.screenshot(region=(x-20, y-20, 40, 40))
            template = np.array(screenshot)
            template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
            
            # Save template for later use
            cv2.imwrite("alch_spell_template.png", template)
            
            self.alch_spell_template = template
            print(f"📍 Alchemy spell template captured at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error capturing alchemy spell template: {e}")
            return False
    
    def capture_arrow_template(self):
        """Capture the arrow template by user positioning"""
        print("🏹 Please move your mouse over the arrows (with number above) and press Enter...")
        input("Press Enter when mouse is over the arrows...")
        
        x, y = pyautogui.position()
        
        # Capture a region around the mouse position
        try:
            screenshot = pyautogui.screenshot(region=(x-30, y-20, 60, 40))
            template = np.array(screenshot)
            template = cv2.cvtColor(template, cv2.COLOR_RGB2BGR)
            
            # Save template for later use
            cv2.imwrite("arrow_template.png", template)
            
            self.arrow_template = template
            print(f"📍 Arrow template captured at ({x}, {y})")
            return True
        except Exception as e:
            print(f"Error capturing arrow template: {e}")
            return False
    
    def load_templates(self):
        """Load saved templates if they exist"""
        try:
            if os.path.exists("alch_spell_template.png"):
                self.alch_spell_template = cv2.imread("alch_spell_template.png")
                print("   📂 Loaded alchemy spell template")
            
            if os.path.exists("arrow_template.png"):
                self.arrow_template = cv2.imread("arrow_template.png")
                print("   📂 Loaded arrow template")
            
            return self.alch_spell_template is not None and self.arrow_template is not None
        except Exception as e:
            print(f"Error loading templates: {e}")
            return False
    
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
        return position, confidence
    
    def detect_arrows(self, screen):
        """Detect arrows using template matching"""
        position, confidence = self.find_template_in_screen(screen, self.arrow_template, threshold=0.7)
        if position:
            print(f"   🏹 Arrows detected at {position} (confidence: {confidence:.2f})")
        return position, confidence
    
    def add_click_variation(self, position):
        """Add random variation to click position"""
        x, y = position
        
        # Randomize variation range for each click - much smaller
        current_variation = random.randint(2, 6)
        
        # Add random variation within the current variation range
        variation_x = random.randint(-current_variation, current_variation)
        variation_y = random.randint(-current_variation, current_variation)
        
        # Rarely add tiny extra randomness
        if random.random() < 0.02:  # 2% chance of tiny extra variation
            variation_x += random.randint(-2, 2)
            variation_y += random.randint(-2, 2)
        
        new_x = x + variation_x
        new_y = y + variation_y
        
        return (new_x, new_y)
    
    def move_and_click(self, position, action_name, instant_click=False):
        """Move mouse to position and click with human-like behavior"""
        try:
            # Add random variation to click position
            varied_position = self.add_click_variation(position)
            x, y = varied_position
            
            # Get current mouse position for path calculation
            current_x, current_y = pyautogui.position()
            
            # Randomize movement speed and style - more realistic
            movement_duration = random.uniform(0.2, 0.8)  # Much faster, more realistic
            
            # Choose movement style randomly - simplified for realism
            movement_style = random.choice(['direct', 'slight_curve'])
            
            if movement_style == 'direct':
                # Direct movement - most common human behavior
                pyautogui.moveTo(x, y, duration=movement_duration)
                
            elif movement_style == 'slight_curve':
                # Single slight curve - occasional human behavior
                mid_x = x + random.randint(-15, 15)
                mid_y = y + random.randint(-15, 15)
                pyautogui.moveTo(mid_x, mid_y, duration=movement_duration * 0.7)
                time.sleep(random.uniform(0.05, 0.15))  # Brief pause
                pyautogui.moveTo(x, y, duration=movement_duration * 0.3)
            
            # Wait time - much more realistic
            if instant_click:
                wait_time = random.uniform(0.02, 0.15)  # Very quick for alch spell
                print(f"   ⚡ Quick click (wait: {wait_time:.2f}s)...")
            else:
                wait_time = random.uniform(0.3, 1.5)  # Realistic wait for arrows
                print(f"   ⏳ Waiting {wait_time:.1f}s before clicking...")
            
            time.sleep(wait_time)
            
            # Click - simplified and realistic
            if random.random() < 0.05:  # 5% chance of slight hesitation
                time.sleep(random.uniform(0.1, 0.3))
                pyautogui.click(x, y)
            else:
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
    
    def take_random_break(self):
        """Take a random break to simulate human behavior"""
        try:
            current_time = time.time()
            session_duration = current_time - self.session_start_time
            
            # Check if it's time for a break (every 10-20 minutes)
            if current_time - self.last_break_time >= self.break_interval:
                break_duration = random.randint(30, 120)  # 30 seconds to 2 minutes
                print(f"   ☕ Taking a {break_duration}s break (session: {session_duration/60:.1f}min)...")
                
                # Move mouse to a random position during break
                random_x = random.randint(100, 800)
                random_y = random.randint(100, 600)
                pyautogui.moveTo(random_x, random_y, duration=random.uniform(0.5, 1.0))
                
                time.sleep(break_duration)
                self.last_break_time = current_time
                print(f"   ✅ Break finished, resuming...")
                return True
            return False
        except Exception as e:
            print(f"Error in random break: {e}")
            return False
    
    def add_natural_mouse_movement(self):
        """Add occasional natural mouse movements"""
        try:
            # 3% chance of random mouse movement
            if random.random() < 0.03:
                # Move to a random position on screen
                random_x = random.randint(100, 1200)
                random_y = random.randint(100, 800)
                
                print(f"   🖱️ Natural mouse movement to ({random_x}, {random_y})...")
                pyautogui.moveTo(random_x, random_y, duration=random.uniform(0.3, 0.8))
                time.sleep(random.uniform(0.5, 2.0))  # Brief pause
                return True
            return False
        except Exception as e:
            print(f"Error in natural mouse movement: {e}")
            return False
    
    def simulate_human_error(self):
        """Occasionally simulate human errors"""
        try:
            # 2% chance of "human error" - click slightly wrong
            if random.random() < 0.02:
                print(f"   🤦 Simulating human error (slight misclick)...")
                time.sleep(random.uniform(0.2, 0.5))
                return True
            return False
        except Exception as e:
            print(f"Error in human error simulation: {e}")
            return False
    
    def start_watching(self):
        """Start the simple template alch clicking process"""
        print("🔍 Starting Advanced Anti-Detection Alch Clicker...")
        print("Step 1: Find alchemy spell")
        print("Step 2: Click spell")
        print("Step 3: Find arrows")
        print("Step 4: Click arrows")
        print("Anti-detection features:")
        print("  ☕ Random breaks (30s-2min every 10-20min)")
        print("  🖱️ Natural mouse movements (3% chance)")
        print("  🤦 Human error simulation (2% chance)")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        
        # Load saved templates (no user input required)
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
                    # Check for changes
                    has_changed = self.detect_change(current_frame, self.previous_screenshot)
                    
                    # Anti-detection features
                    self.take_random_break()
                    self.add_natural_mouse_movement()
                    self.simulate_human_error()
                    
                    # Only act if enough time has passed since last action
                    # Randomize cooldown for each cycle - more realistic
                    current_cooldown = random.uniform(0.1, 0.5)
                    if current_time - self.last_action_time >= current_cooldown:
                        
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
                print("\n🛑 Stopping Simple Template Alch Clicker...")
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
    """Main function to run the Advanced Anti-Detection Alch Clicker"""
    print("🤖 Advanced Anti-Detection Alch Clicker - Human-like Behavior")
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
    
    # Create and start the Simple Template Alch Clicker
    clicker = SimpleTemplateAlch()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

