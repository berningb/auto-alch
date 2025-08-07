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

class HighAlchClicker:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        self.last_click_time = 0
        self.click_interval = random.randint(1, 15)  # Random interval between 1-15 seconds
        self.click_count = 0
        
        # Default position for arrow clicking (you can adjust these coordinates)
        # These are example coordinates - you'll need to set the actual position
        self.arrow_x = 800  # X coordinate for arrow position
        self.arrow_y = 400  # Y coordinate for arrow position
        
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
    
    def set_arrow_position(self):
        """Set the arrow position by getting current mouse position"""
        print("🖱️  Please move your mouse to the arrow position and press Enter...")
        input("Press Enter when mouse is over the arrows...")
        
        x, y = pyautogui.position()
        self.arrow_x = x
        self.arrow_y = y
        
        print(f"📍 Arrow position set to: ({x}, {y})")
        return True
    
    def click_arrows(self):
        """Click on the arrows for high alching"""
        try:
            # Click on the arrow position
            pyautogui.click(self.arrow_x, self.arrow_y)
            
            self.click_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🏹 Clicked arrows #{self.click_count} at ({self.arrow_x}, {self.arrow_y})")
            
            return True
                
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
            changed_pixels = np.count_nonzero(diff > 30)  # Threshold for significant change
            change_percentage = changed_pixels / total_pixels
            
            return change_percentage > threshold
            
        except Exception as e:
            print(f"Error detecting change: {e}")
            return False
    
    def analyze_screen_content(self, frame):
        """Basic analysis of screen content"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Basic edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Count edge pixels (basic measure of visual complexity)
            edge_pixels = np.count_nonzero(edges)
            total_pixels = edges.shape[0] * edges.shape[1]
            edge_density = edge_pixels / total_pixels
            
            # Basic brightness analysis
            brightness = np.mean(gray)
            
            return {
                'edge_density': edge_density,
                'brightness': brightness,
                'has_content': edge_density > 0.01 or brightness > 50
            }
            
        except Exception as e:
            print(f"Error analyzing screen content: {e}")
            return {'has_content': False}
    
    def start_watching(self):
        """Start the screen watching and arrow clicking process"""
        print("🔍 Starting High Alch Arrow Clicker...")
        print("I'm watching your screen and will click arrows for high alching every 1-15 seconds!")
        print("Press Ctrl+C to stop.")
        print("Move mouse to corner to emergency stop.")
        
        # Set arrow position first
        if not self.set_arrow_position():
            print("❌ Failed to set arrow position")
            return
        
        self.is_watching = True
        self.previous_screenshot = None
        self.last_click_time = time.time()
        
        while self.is_watching:
            try:
                current_time = time.time()
                
                # Capture current screen
                current_frame = self.capture_screen()
                
                if current_frame is not None:
                    # Analyze screen content
                    analysis = self.analyze_screen_content(current_frame)
                    
                    # Check for changes
                    has_changed = self.detect_change(current_frame, self.previous_screenshot)
                    
                    # Respond to visual input
                    if has_changed and analysis['has_content']:
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] 👁️  I can see! Screen content detected!")
                        
                        # Additional analysis
                        if analysis['edge_density'] > 0.05:
                            print(f"   📊 High visual complexity detected")
                        if analysis['brightness'] > 150:
                            print(f"   💡 Bright screen detected")
                        elif analysis['brightness'] < 50:
                            print(f"   🌙 Dark screen detected")
                    
                    # Check if it's time to click arrows
                    if current_time - self.last_click_time >= self.click_interval:
                        if self.click_arrows():
                            # Set new random interval for next click
                            self.click_interval = random.randint(1, 15)
                            self.last_click_time = current_time
                            print(f"   ⏰ Next click in {self.click_interval} seconds")
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping High Alch Clicker...")
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
    """Main function to run the High Alch Clicker"""
    print("🤖 High Alch Arrow Clicker - AI-Inspired Screen Watcher")
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
    
    # Create and start the High Alch Clicker
    clicker = HighAlchClicker()
    
    try:
        clicker.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()


