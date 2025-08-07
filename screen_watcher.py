import cv2
import numpy as np
import pyautogui
import time
from datetime import datetime
import os

class ScreenWatcher:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        
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
        """Start the screen watching process"""
        print("🔍 Starting screen watcher...")
        print("I'm watching your screen! Press Ctrl+C to stop.")
        
        self.is_watching = True
        self.previous_screenshot = None
        
        while self.is_watching:
            try:
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
                    
                    # Update previous frame
                    self.previous_screenshot = current_frame.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\n🛑 Stopping screen watcher...")
                self.is_watching = False
                break
            except Exception as e:
                print(f"Error in watching loop: {e}")
                time.sleep(1)
    
    def stop_watching(self):
        """Stop the screen watching process"""
        self.is_watching = False

def main():
    """Main function to run the screen watcher"""
    print("🤖 Basic AI-Inspired Screen Watcher")
    print("=" * 40)
    
    # Check if required packages are available
    try:
        import cv2
        import pyautogui
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install required packages:")
        print("pip install opencv-python pyautogui numpy")
        return
    
    # Create and start the screen watcher
    watcher = ScreenWatcher()
    
    try:
        watcher.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()



