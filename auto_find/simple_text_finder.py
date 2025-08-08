#!/usr/bin/env python3
"""
Simple Text Finder - No External OCR Required
Uses template matching and color detection to find text-like elements
"""

import sys
import os
import time
import random

# Add the auto_actions directory to Python path so we can import funcs
auto_actions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auto_actions')
sys.path.append(auto_actions_dir)

try:
    import cv2
    import numpy as np
    import pyautogui
    from pynput import keyboard
    from funcs import AutoActionFunctions
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Install with: pip install opencv-python numpy pyautogui pynput")
    sys.exit(1)


class SimpleTextFinder:
    def __init__(self):
        self.functions = AutoActionFunctions()
        self.is_paused = True
        
        # Configure pyautogui safety
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True
    
    def wait_for_unpause(self):
        """Wait for user to press 'p' to continue"""
        print("⏸️  PAUSED - Click into your game screen and press 'p' to start")
        
        self.is_paused = True
        
        def on_key_press(key):
            try:
                if key.char == 'p':
                    self.is_paused = False
                    print("▶️  UNPAUSED - Starting action...")
                    return False  # Stop listener
            except AttributeError:
                pass
        
        listener = keyboard.Listener(on_press=on_key_press)
        listener.start()
        
        while self.is_paused:
            time.sleep(0.1)
        
        listener.stop()
    
    def findtextonscreen(self, target_text=None, click=True, pause=True, color_range="all", template_path=None):
        """
        Find text-like elements on screen using template matching or color detection
        
        Args:
            target_text (str): For display purposes (not actually used for detection)
            click (bool): Whether to click on found element
            pause (bool): Whether to pause and wait for 'p' key
            color_range (str): "white", "yellow", "red", "green", "blue", or "all"
            template_path (str): Path to a template image to match instead of color detection
            
        Returns:
            dict: Result with success status and details
        """
        
        if pause:
            if target_text:
                print(f"🔍 Preparing to search for: '{target_text}'")
            elif template_path:
                print(f"🔍 Preparing to search for template: {template_path}")
            else:
                print(f"🔍 Preparing to search for {color_range} text elements")
            self.wait_for_unpause()
        
        try:
            # Capture screen
            screen = self.functions.capture_screen()
            if screen is None:
                return {
                    'success': False,
                    'error': 'Failed to capture screen',
                    'position': None
                }
            
            if template_path and os.path.exists(template_path):
                # Use template matching
                return self._template_match(screen, template_path, click)
            else:
                # Use color-based text detection
                return self._color_based_detection(screen, color_range, click, target_text)
        
        except Exception as e:
            error_msg = f"Error during detection: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'position': None
            }
    
    def _template_match(self, screen, template_path, click):
        """Match a template image on screen"""
        try:
            template = cv2.imread(template_path)
            if template is None:
                return {
                    'success': False,
                    'error': f'Could not load template: {template_path}',
                    'position': None
                }
            
            # Find template on screen
            position, confidence = self.functions.find_template(screen, template, threshold=0.6)
            
            if position:
                print(f"✅ Found template match at {position} (confidence: {confidence:.2f})")
                
                if click:
                    # Add randomness to click
                    x, y = position
                    offset_x = random.randint(-5, 5)
                    offset_y = random.randint(-3, 3)
                    final_x = x + offset_x
                    final_y = y + offset_y
                    
                    print(f"🖱️  Clicking at ({final_x}, {final_y})")
                    pyautogui.moveTo(final_x, final_y, duration=0.3)
                    time.sleep(0.1)
                    pyautogui.click()
                    print("✅ Clicked on template match")
                
                return {
                    'success': True,
                    'position': position,
                    'confidence': confidence,
                    'method': 'template_match'
                }
            else:
                return {
                    'success': False,
                    'error': 'Template not found on screen',
                    'position': None
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Template matching error: {e}',
                'position': None
            }
    
    def _color_based_detection(self, screen, color_range, click, target_text):
        """Detect text-like elements based on color"""
        try:
            # Convert to HSV for better color filtering
            hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
            
            # Define color ranges (HSV)
            color_ranges = {
                'white': [(0, 0, 200), (179, 30, 255)],
                'yellow': [(20, 100, 100), (30, 255, 255)],
                'red': [(0, 120, 70), (10, 255, 255)],
                'green': [(40, 40, 40), (80, 255, 255)],
                'blue': [(100, 150, 0), (130, 255, 255)],
            }
            
            found_elements = []
            
            if color_range == "all":
                # Check all colors
                colors_to_check = list(color_ranges.keys())
            else:
                # Check specific color
                colors_to_check = [color_range] if color_range in color_ranges else ['white']
            
            for color_name in colors_to_check:
                if color_name not in color_ranges:
                    continue
                
                lower, upper = color_ranges[color_name]
                lower = np.array(lower)
                upper = np.array(upper)
                
                # Create mask for this color
                mask = cv2.inRange(hsv, lower, upper)
                
                # Find contours (text-like shapes)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    # Filter by size (text-like dimensions)
                    x, y, w, h = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)
                    
                    # Text-like criteria: reasonable size, not too thin/thick
                    if (10 < w < 200 and 8 < h < 50 and 
                        area > 50 and 
                        0.1 < h/w < 3):  # Aspect ratio filter
                        
                        center_x = x + w // 2
                        center_y = y + h // 2
                        
                        found_elements.append({
                            'position': (center_x, center_y),
                            'size': (w, h),
                            'area': area,
                            'color': color_name
                        })
                        
                        print(f"✅ Found {color_name} text-like element at ({center_x}, {center_y}) size: {w}x{h}")
            
            if not found_elements:
                error_msg = f"No text-like elements found"
                if target_text:
                    error_msg += f" for '{target_text}'"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'position': None
                }
            
            # Sort by area (larger text elements first)
            found_elements.sort(key=lambda x: x['area'], reverse=True)
            best_element = found_elements[0]
            
            print(f"🎯 Best match: {best_element['color']} element at {best_element['position']}")
            
            if click:
                x, y = best_element['position']
                offset_x = random.randint(-3, 3)
                offset_y = random.randint(-2, 2)
                final_x = x + offset_x
                final_y = y + offset_y
                
                print(f"🖱️  Clicking at ({final_x}, {final_y})")
                pyautogui.moveTo(final_x, final_y, duration=0.3)
                time.sleep(0.1)
                pyautogui.click()
                print("✅ Clicked on text element")
            
            return {
                'success': True,
                'position': best_element['position'],
                'size': best_element['size'],
                'color': best_element['color'],
                'all_found': found_elements,
                'method': 'color_detection'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Color detection error: {e}',
                'position': None
            }
    
    def create_text_template(self, save_path):
        """Helper to create a template from screen selection"""
        print("🖼️  Template Creator")
        print("This will help you create a template for the text you want to find")
        print("1. Position your screen so the text is visible")
        print("2. Press 'p' when ready")
        print("3. You'll have 3 seconds to hover over the text")
        print("4. We'll capture that area as a template")
        
        self.wait_for_unpause()
        
        print("⏰ Get ready to hover over your target text...")
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Get mouse position
        x, y = pyautogui.position()
        print(f"📍 Mouse position: ({x}, {y})")
        
        # Capture screen
        screen = self.functions.capture_screen()
        if screen is None:
            print("❌ Failed to capture screen")
            return False
        
        # Extract area around mouse (adjust size as needed)
        template_size = 100
        x1 = max(0, x - template_size // 2)
        y1 = max(0, y - template_size // 2)
        x2 = min(screen.shape[1], x + template_size // 2)
        y2 = min(screen.shape[0], y + template_size // 2)
        
        template = screen[y1:y2, x1:x2]
        
        # Save template
        cv2.imwrite(save_path, template)
        print(f"✅ Template saved to: {save_path}")
        print(f"   Template size: {template.shape[1]}x{template.shape[0]}")
        
        return True


def quick_test():
    """Quick test function"""
    finder = SimpleTextFinder()
    
    print("🧪 Simple Text Finder Test")
    print("=" * 40)
    print("Choose detection method:")
    print("1. Color-based detection (no templates needed)")
    print("2. Template matching (you provide template image)")
    print("3. Create new template from screen")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        print("\nAvailable colors: white, yellow, red, green, blue, all")
        color = input("Enter color to detect (default: white): ").strip() or "white"
        
        click_option = input("Click on found element? (y/n, default: y): ").strip().lower()
        should_click = click_option != 'n'
        
        result = finder.findtextonscreen(
            target_text=f"{color} text", 
            click=should_click, 
            color_range=color
        )
        
        print(f"\n📊 Result: {result}")
    
    elif choice == '2':
        template_path = input("Enter path to template image: ").strip()
        if not template_path or not os.path.exists(template_path):
            print("❌ Template file not found")
            return
        
        click_option = input("Click on found template? (y/n, default: y): ").strip().lower()
        should_click = click_option != 'n'
        
        result = finder.findtextonscreen(
            template_path=template_path,
            click=should_click
        )
        
        print(f"\n📊 Result: {result}")
    
    elif choice == '3':
        save_path = input("Enter path to save template (e.g., templates/my_text.png): ").strip()
        if not save_path:
            save_path = "text_template.png"
        
        # Create directory if needed
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
        
        finder.create_text_template(save_path)
    
    elif choice == '4':
        print("👋 Goodbye!")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    quick_test()
