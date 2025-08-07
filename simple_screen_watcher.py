import time
from datetime import datetime
import os
import sys

# Try to import PIL (Pillow) which is often pre-installed
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available. Install with: python -m pip install Pillow")

class SimpleScreenWatcher:
    def __init__(self):
        self.previous_screenshot = None
        self.is_watching = False
        
    def capture_screen(self):
        """Capture the current screen using PIL"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            screenshot = ImageGrab.grab()
            return screenshot
        except Exception as e:
            print(f"Error capturing screen: {e}")
            return None
    
    def detect_change(self, current_screenshot, previous_screenshot, threshold=0.1):
        """Detect if there's a significant change between screenshots"""
        if previous_screenshot is None:
            return True
        
        try:
            # Convert to grayscale for comparison
            current_gray = current_screenshot.convert('L')
            previous_gray = previous_screenshot.convert('L')
            
            # Get pixel data
            current_data = list(current_gray.getdata())
            previous_data = list(previous_gray.getdata())
            
            # Calculate difference
            total_pixels = len(current_data)
            changed_pixels = sum(1 for i in range(total_pixels) 
                               if abs(current_data[i] - previous_data[i]) > 30)
            
            change_percentage = changed_pixels / total_pixels
            return change_percentage > threshold
            
        except Exception as e:
            print(f"Error detecting change: {e}")
            return False
    
    def analyze_screen_content(self, screenshot):
        """Basic analysis of screen content"""
        try:
            # Convert to grayscale
            gray = screenshot.convert('L')
            
            # Get pixel data
            pixels = list(gray.getdata())
            
            # Calculate brightness
            brightness = sum(pixels) / len(pixels)
            
            # Simple edge detection (count pixels that differ significantly from neighbors)
            width, height = gray.size
            edge_count = 0
            total_pixels = width * height
            
            for y in range(1, height - 1):
                for x in range(1, width - 1):
                    center = pixels[y * width + x]
                    left = pixels[y * width + (x - 1)]
                    right = pixels[y * width + (x + 1)]
                    top = pixels[(y - 1) * width + x]
                    bottom = pixels[(y + 1) * width + x]
                    
                    # Check if this pixel is significantly different from neighbors
                    if (abs(center - left) > 30 or abs(center - right) > 30 or 
                        abs(center - top) > 30 or abs(center - bottom) > 30):
                        edge_count += 1
            
            edge_density = edge_count / total_pixels
            
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
        print("🔍 Starting simple screen watcher...")
        print("I'm watching your screen! Press Ctrl+C to stop.")
        
        if not PIL_AVAILABLE:
            print("❌ PIL/Pillow is required for screen capture.")
            print("Install it with: python -m pip install Pillow")
            return
        
        self.is_watching = True
        self.previous_screenshot = None
        
        while self.is_watching:
            try:
                # Capture current screen
                current_screenshot = self.capture_screen()
                
                if current_screenshot is not None:
                    # Analyze screen content
                    analysis = self.analyze_screen_content(current_screenshot)
                    
                    # Check for changes
                    has_changed = self.detect_change(current_screenshot, self.previous_screenshot)
                    
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
                    
                    # Update previous screenshot
                    self.previous_screenshot = current_screenshot.copy()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1)
                
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
    """Main function to run the simple screen watcher"""
    print("🤖 Simple AI-Inspired Screen Watcher")
    print("=" * 40)
    
    # Create and start the screen watcher
    watcher = SimpleScreenWatcher()
    
    try:
        watcher.start_watching()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()



