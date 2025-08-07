import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
import random
import os

# Configure pyautogui for safety
pyautogui.FAILSAFE = True  # Move mouse to corner to stop
pyautogui.PAUSE = 0.1  # Small pause between actions

class AutoFinderClicker:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.click_count = 0
        self.last_action_time = 0
        self.action_cooldown = 0.5  # Minimum time between actions
        
        # State tracking
        self.waiting_for_alch_symbol = True
        self.waiting_for_arrows = False
        
        # Click variation settings
        self.click_variation = 15  # Pixels to vary from center
        
        # Known alch symbol and arrow patterns (we'll create these)
        self.alch_patterns = []
        self.arrow_patterns = []
        
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
    
    def create_alch_patterns(self):
        """Create patterns to recognize alch symbols"""
        # Common alch symbol patterns (you can add more)
        patterns = [
            # High alch spell icon pattern (basic shape)
            np.array([
                [255, 255, 255, 255, 255],
                [255, 200, 150, 200, 255],
                [255, 150, 100, 150, 255],
                [255, 200, 150, 200, 255],
                [255, 255, 255, 255, 255]
            ], dtype=np.uint8)
        ]
        return patterns
    
    def create_arrow_patterns(self):
        """Create patterns to recognize arrows"""
        # Common arrow patterns
        patterns = [
            # Arrow icon pattern
            np.array([
                [255, 255, 255, 255, 255],
                [255, 255, 200, 255, 255],
                [255, 200, 150, 200, 255],
                [255, 255, 200, 255, 255],
                [255, 255, 255, 255, 255]
            ], dtype=np.uint8)
        ]
        return patterns
    
    def find_patterns_in_screen(self, screen, patterns, threshold=0.7):
        """Find patterns in screen using template matching"""
        try:
            screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
            
            for pattern in patterns:
                # Resize pattern to different scales for better detection
                for scale in [0.8, 1.0, 1.2]:
                    scaled_pattern = cv2.resize(pattern, None, fx=scale, fy=scale)
                    
                    # Perform template matching
                    result = cv2.matchTemplate(screen_gray, scaled_pattern, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val >= threshold:
                        # Return center of matched region
                        h, w = scaled_pattern.shape
                        center_x = max_loc[0] + w // 2
                        center_y = max_loc[1] + h // 2
                        return (center_x, center_y), max_val
            
            return None, 0
                
        except Exception as e:
            print(f"Error in pattern matching: {e}")
            return None, 0
    
    def detect_alch_symbol_auto(self, screen):
        """Automatically detect alch symbols on screen"""
        if not self.alch_patterns:
            self.alch_patterns = self.create_alch_patterns()
        
        position, confidence = self.find_patterns_in_screen(screen, self.alch_patterns)
        return position, confidence
    
    def detect_arrows_auto(self, screen):
        """Automatically detect arrows on screen"""
        if not self.arrow_patterns:
            self.arrow_patterns = self.create_arrow_patterns()
        
        position, confidence = self.find_patterns_in_screen(screen, self.arrow_patterns)
        return position, confidence
    
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
            
            # Move mouse to the position (faster movement)
            pyautogui.moveTo(x, y, duration=random.uniform(0.8, 1.2))
            
            # Wait time depends on whether it's instant or not
            if instant_click:
                wait_time = 0.1  # Almost instant for alch symbol
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
    
    def click_alch_symbol(self, position):
        """Click on the alch symbol with instant behavior"""
        return self.move_and_click(position, "🔮 Clicked alch symbol", instant_click=True)
    
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
        """Start the auto-finding alch clicking process"""
        print("🔍 Starting Auto-Finder Alch Clicker...")
        print("I'm automatically finding and clicking alch symbols and arrows!")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        
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
                        
                        if self.waiting_for_alch_symbol:
                            # Look for alch symbol automatically
                            alch_position, alch_confidence = self.detect_alch_symbol_auto(current_frame)
                            
                            if alch_position and alch_confidence > 0.7:
                                print(f"   🔍 Alch symbol auto-detected (confidence: {alch_confidence:.2f})")
                                if self.click_alch_symbol(alch_position):
                                    self.waiting_for_alch_symbol = False
                                    self.waiting_for_arrows = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for arrows...")
                        
                        elif self.waiting_for_arrows:
                            # Look for arrows automatically
                            arrow_position, arrow_confidence = self.detect_arrows_auto(current_frame)
                            
                            if arrow_position and arrow_confidence > 0.7:
                                print(f"   🔍 Arrows auto-detected (confidence: {arrow_confidence:.2f})")
                                if self.click_arrows(arrow_position):
                                    self.waiting_for_alch_symbol = True
                                    self.waiting_for_arrows = False
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for alch symbol...")
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)  # Faster response time for template matching
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping Auto-Finder Alch Clicker...")
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
    """Main function to run the Auto-Finder Alch Clicker"""
    print("🤖 Auto-Finder Alch Clicker - AI-Inspired Screen Watcher")
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
    
    # Create and start the Auto-Finder Alch Clicker
    clicker = AutoFinderClicker()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()

