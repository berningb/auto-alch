#!/usr/bin/env python3
"""
Test script for crab detection and clicking
"""

import cv2
import numpy as np
import pyautogui
import time
import os
import sys

# Add auto_actions to path
auto_actions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_actions")
sys.path.append(auto_actions_dir)

# Configure pyautogui for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

class CrabDetectionTester:
    def __init__(self):
        self.crab_templates = None
        self.debug = True
        
        # Color-based detection settings for crabs
        self.crab_hsv_lower = np.array([80, 120, 120])  # Cyan color range (FF00FFFF)
        self.crab_hsv_upper = np.array([100, 255, 255])
        
        # Area constraints
        self.min_area_crab = 500.0
        self.max_area_crab = 50000.0
        self.edge_margin = 2
        
    def load_crab_templates(self):
        """Load crab template images"""
        templates = []
        current_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(current_dir, "auto_alch", "images")
        
        # Look for crab*.png files
        import glob
        pattern = os.path.join(images_dir, "crab*.png")
        template_files = glob.glob(pattern)
        
        # Also check current directory
        current_pattern = os.path.join(current_dir, "crab*.png")
        template_files.extend(glob.glob(current_pattern))
        
        template_files = sorted(list(set(template_files)))
        
        for template_file in template_files:
            try:
                template = cv2.imread(template_file)
                if template is not None:
                    templates.append(template)
                    filename = os.path.basename(template_file)
                    print(f"✅ Loaded crab template: {filename}")
                else:
                    print(f"❌ Failed to load {template_file}")
            except Exception as e:
                print(f"❌ Error loading {template_file}: {e}")
        
        self.crab_templates = templates
        return len(templates) > 0
    
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
    
    def find_crab_by_template(self, screen):
        """Find crab using template matching"""
        if not self.crab_templates:
            print("❌ No crab templates loaded")
            return None, 0.0
        
        best_result = None
        best_confidence = 0.0
        best_template_index = -1
        
        for i, template in enumerate(self.crab_templates):
            result, confidence = self.find_template(screen, template, threshold=0.3)
            if confidence > best_confidence:
                best_confidence = confidence
                best_result = result
                best_template_index = i
        
        if best_result and best_confidence > 0.3:
            print(f"   📊 Using crab template {best_template_index + 1} (confidence: {best_confidence:.2f})")
            return best_result, best_confidence
        
        print(f"   📊 Best crab template match: {best_confidence:.2f}")
        return None, best_confidence
    
    def find_crab_by_color(self, screen):
        """Find crab using color detection"""
        try:
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, self.crab_hsv_lower, self.crab_hsv_upper)
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
            mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, kernel, iterations=1)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                print("   🎨 No cyan contours found")
                return None, 0.0

            # Pick the largest valid cyan region
            h_img, w_img = screen.shape[:2]
            best_region = None
            best_area = 0.0
            for c in contours:
                area = float(cv2.contourArea(c))
                if area < self.min_area_crab or area > self.max_area_crab:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                if x <= self.edge_margin or y <= self.edge_margin or (x + w) >= (w_img - self.edge_margin) or (y + h) >= (h_img - self.edge_margin):
                    continue
                if area > best_area:
                    best_area = area
                    best_region = (x, y, w, h)

            if best_region is None:
                print("   🎨 No valid cyan regions found")
                return None, 0.0

            x, y, w, h = best_region
            cx, cy = x + w // 2, y + h // 2

            print(f"   🦀 Crab region detected at ({cx}, {cy}) (area: {int(best_area)})")
            return (cx, cy), 0.8

        except Exception as e:
            print(f"   ❌ Error in color-based crab detection: {e}")
            return None, 0.0
    
    def find_crab(self, screen):
        """Find crab using color detection as primary method"""
        print("🔍 Testing crab detection...")
        
        # Try color detection first (since template isn't working well)
        print("   🎨 Trying color detection...")
        color_pos, color_conf = self.find_crab_by_color(screen)
        if color_pos is not None and color_conf > 0.5:
            print(f"   ✅ Found crab with color detection (confidence: {color_conf:.2f})")
            return color_pos, color_conf
        
        # Fallback to template matching
        print("   📋 Color detection failed, trying template matching...")
        crab_position, crab_confidence = self.find_crab_by_template(screen)
        if crab_position and crab_confidence > 0.3:
            print(f"   ✅ Found crab with template (confidence: {crab_confidence:.2f})")
            return crab_position, crab_confidence
        
        print("   ❌ No crab found")
        return None, max(color_conf, crab_confidence)
    
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
    
    def click_crab(self, position):
        """Click on crab position"""
        try:
            x, y = position
            print(f"🖱️ Clicking crab at ({x}, {y})")
            pyautogui.click(x, y)
            print("✅ Clicked crab!")
            return True
        except Exception as e:
            print(f"❌ Error clicking crab: {e}")
            return False
    
    def run_test(self):
        """Run the crab detection test"""
        print("🦀 Crab Detection Test")
        print("=" * 40)
        
        # Load templates
        if not self.load_crab_templates():
            print("❌ Failed to load crab templates")
            return
        
        print("\n📋 Instructions:")
        print("1. Make sure a crab is visible on screen")
        print("2. Press Enter to start detection")
        print("3. The script will try to find and click the crab")
        print("4. Press Ctrl+C to stop")
        print()
        
        input("Press Enter to start crab detection...")
        
        while True:
            try:
                print("\n" + "="*50)
                
                # Capture screen
                screen = self.capture_screen()
                if screen is None:
                    print("❌ Could not capture screen")
                    time.sleep(1)
                    continue
                
                # Find crab
                crab_position, crab_confidence = self.find_crab(screen)
                
                if crab_position and crab_confidence > 0.5:
                    print(f"🎯 Crab found! Confidence: {crab_confidence:.2f}")
                    
                    # Ask user if they want to click
                    response = input("Click on the crab? (y/n): ").lower().strip()
                    if response == 'y':
                        if self.click_crab(crab_position):
                            print("✅ Successfully clicked crab!")
                        else:
                            print("❌ Failed to click crab")
                    else:
                        print("⏭️ Skipped clicking")
                else:
                    print(f"❌ No crab found (best confidence: {crab_confidence:.2f})")
                
                # Wait before next detection
                print("⏳ Waiting 3 seconds before next detection...")
                time.sleep(3)
                
            except KeyboardInterrupt:
                print("\n🛑 Test stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(1)

def main():
    """Main function"""
    print("Starting Crab Detection Test...")
    
    # Check imports
    try:
        import cv2
        import pyautogui
        import numpy as np
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Install with: pip install opencv-python pyautogui numpy")
        return
    
    # Create and run tester
    tester = CrabDetectionTester()
    tester.run_test()

if __name__ == "__main__":
    main()
