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

class RuneLiteSpecificClicker:
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
        
        # RuneLite window bounds
        self.runelite_window = None
        
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
    
    def find_runelite_window(self):
        """Find RuneLite window on screen"""
        try:
            # Look for RuneLite window by title
            windows = pyautogui.getWindowsWithTitle("RuneLite")
            if windows:
                return windows[0]
            
            # Also try variations of the name
            windows = pyautogui.getWindowsWithTitle("runelite")
            if windows:
                return windows[0]
                
            # Try partial matches
            all_windows = pyautogui.getAllWindows()
            for window in all_windows:
                if window.title and ("runelite" in window.title.lower() or "runescape" in window.title.lower()):
                    return window
                    
            return None
        except Exception as e:
            print(f"Error finding RuneLite window: {e}")
            return None
    
    def capture_runelite_region(self):
        """Capture only the RuneLite window region"""
        if not self.runelite_window:
            self.runelite_window = self.find_runelite_window()
        
        if self.runelite_window:
            try:
                # Capture only the RuneLite window
                x, y, width, height = (self.runelite_window.left, self.runelite_window.top, 
                                     self.runelite_window.width, self.runelite_window.height)
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                return frame, (x, y)  # Return frame and offset
            except Exception as e:
                print(f"Error capturing RuneLite region: {e}")
                return None, (0, 0)
        return None, (0, 0)
    
    def detect_alch_symbol_in_runelite(self, frame, offset):
        """Detect the High Alch spell icon in RuneLite"""
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Look for orange/yellow fire-like colors (High Alch spell)
            # Orange/Yellow range in HSV
            lower_orange = np.array([10, 100, 100])
            upper_orange = np.array([25, 255, 255])
            
            # Create mask for orange/yellow colors
            mask = cv2.inRange(hsv, lower_orange, upper_orange)
            
            # Find contours in the mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for the largest orange/yellow region (likely the alch spell)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest_contour)
                
                # Only consider reasonably sized regions
                if area > 100:  # Minimum area threshold
                    # Get the center of the contour
                    M = cv2.moments(largest_contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + offset[0]
                        cy = int(M["m01"] / M["m00"]) + offset[1]
                        return (cx, cy), 0.9  # High confidence for color-based detection
            
            return None, 0
                
        except Exception as e:
            print(f"Error detecting alch symbol: {e}")
            return None, 0
    
    def detect_arrows_in_runelite(self, frame, offset):
        """Detect arrow items in RuneLite"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Look for greyed-out arrow shapes
            # Use edge detection to find arrow-like shapes
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours in the edges
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for small, pointed shapes (arrows)
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Look for small arrow-sized regions
                if 50 < area < 500:  # Reasonable size for arrow icons
                    # Get the center of the contour
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + offset[0]
                        cy = int(M["m01"] / M["m00"]) + offset[1]
                        
                        # Check if this region is greyed out (low brightness)
                        x, y, w, h = cv2.boundingRect(contour)
                        roi = gray[y:y+h, x:x+w]
                        if roi.size > 0:
                            avg_brightness = np.mean(roi)
                            # Greyed out items have lower brightness
                            if avg_brightness < 150:  # Threshold for greyed out
                                return (cx, cy), 0.8
            
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
    
    def start_watching(self):
        """Start the RuneLite-specific alch clicking process"""
        print("🔍 Starting RuneLite-Specific Alch Clicker...")
        print("I'm watching the RuneLite window for alch symbols and arrows!")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        print(f"🎯 Click variation: ±{self.click_variation} pixels from center")
        
        # Find RuneLite window first
        self.runelite_window = self.find_runelite_window()
        if not self.runelite_window:
            print("❌ RuneLite window not found! Please make sure RuneLite is running.")
            return
        
        print(f"📍 Found RuneLite window: {self.runelite_window.title}")
        
        self.is_watching = True
        self.previous_screenshot = None
        self.last_action_time = time.time()
        
        while self.is_watching:
            try:
                current_time = time.time()
                
                # Capture only the RuneLite window
                current_frame, offset = self.capture_runelite_region()
                
                if current_frame is not None:
                    # Only act if enough time has passed since last action
                    if current_time - self.last_action_time >= self.action_cooldown:
                        
                        if self.waiting_for_alch_symbol:
                            # Look for alch symbol in RuneLite
                            alch_position, alch_confidence = self.detect_alch_symbol_in_runelite(current_frame, offset)
                            
                            if alch_position and alch_confidence > 0.8:
                                print(f"   🔍 Alch symbol detected in RuneLite (confidence: {alch_confidence:.2f})")
                                if self.click_alch_symbol(alch_position):
                                    self.waiting_for_alch_symbol = False
                                    self.waiting_for_arrows = True
                                    self.last_action_time = current_time
                                    print("   🔄 Now waiting for arrows...")
                        
                        elif self.waiting_for_arrows:
                            # Look for arrows in RuneLite
                            arrow_position, arrow_confidence = self.detect_arrows_in_runelite(current_frame, offset)
                            
                            if arrow_position and arrow_confidence > 0.7:
                                print(f"   🔍 Arrows detected in RuneLite (confidence: {arrow_confidence:.2f})")
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
                print("\n🛑 Stopping RuneLite-Specific Alch Clicker...")
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
    """Main function to run the RuneLite-Specific Alch Clicker"""
    print("🤖 RuneLite-Specific Alch Clicker - AI-Inspired Screen Watcher")
    print("=" * 65)
    
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
    
    # Create and start the RuneLite-Specific Alch Clicker
    clicker = RuneLiteSpecificClicker()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
