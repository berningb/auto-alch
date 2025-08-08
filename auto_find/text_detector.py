#!/usr/bin/env python3
"""
Text Detection Script for NPCs, Items, and Interface Elements
Finds text on screen and clicks on it with pause/unpause functionality
"""

import sys
import os
import time
import random
from datetime import datetime

# Add the auto_actions directory to Python path so we can import funcs
auto_actions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auto_actions')
sys.path.append(auto_actions_dir)

try:
    import cv2
    import numpy as np
    import pyautogui
    import pytesseract
    from pynput import keyboard
    from funcs import AutoActionFunctions
except ImportError as e:
    print(f"❌ Error importing required modules: {e}")
    print("Install missing packages with:")
    print("pip install opencv-python numpy pyautogui pytesseract pynput")
    print("Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
    sys.exit(1)


class TextDetector:
    def __init__(self):
        self.functions = AutoActionFunctions()
        self.is_paused = True
        
        # Configure pyautogui safety
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True
        
        # Configure tesseract if needed (adjust path for your system)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def wait_for_pause_unpause(self, action_description):
        """Wait for user to press 'p' to start action"""
        print(f"⏸️  PAUSED - {action_description}")
        print("   Click into your game screen and press 'p' to start")
        
        self.is_paused = True
        
        def on_key_press(key):
            try:
                if key.char == 'p':
                    self.is_paused = False
                    print("▶️  UNPAUSED - Starting text detection...")
                    return False  # Stop listener
            except AttributeError:
                pass
        
        listener = keyboard.Listener(on_press=on_key_press)
        listener.start()
        
        while self.is_paused:
            time.sleep(0.1)
        
        listener.stop()
    
    def findtextonscreen(self, target_text, click=True, confidence_threshold=0.7, case_sensitive=False):
        """
        Find specific text on screen using OCR and optionally click on it
        
        Args:
            target_text (str): The text to search for
            click (bool): Whether to click on the found text
            confidence_threshold (float): Minimum confidence for text detection (0.0-1.0)
            case_sensitive (bool): Whether search should be case sensitive
            
        Returns:
            dict: Result with success status, position, and details
        """
        try:
            print(f"🔍 Searching for text: '{target_text}'")
            print(f"📊 Settings: click={click}, confidence≥{confidence_threshold}, case_sensitive={case_sensitive}")
            
            # Capture screen
            screen = self.functions.capture_screen()
            if screen is None:
                return {
                    'success': False,
                    'error': 'Failed to capture screen',
                    'position': None,
                    'confidence': 0
                }
            
            # Convert to format suitable for OCR
            # Convert BGR to RGB for tesseract
            screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
            
            # Use tesseract to extract text with bounding boxes
            data = pytesseract.image_to_data(screen_rgb, output_type=pytesseract.Output.DICT)
            
            # Prepare search text
            search_text = target_text if case_sensitive else target_text.lower()
            
            # Search through detected text
            found_matches = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:  # Skip empty text
                    continue
                
                # Apply case sensitivity
                compare_text = text if case_sensitive else text.lower()
                
                # Check for exact match or partial match
                confidence = float(data['conf'][i]) / 100.0  # Convert to 0-1 scale
                
                if search_text in compare_text and confidence >= confidence_threshold:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    match = {
                        'text': text,
                        'position': (center_x, center_y),
                        'bounding_box': (x, y, w, h),
                        'confidence': confidence
                    }
                    found_matches.append(match)
                    
                    print(f"✅ Found '{text}' at ({center_x}, {center_y}) with {confidence:.2f} confidence")
            
            if not found_matches:
                print(f"❌ Text '{target_text}' not found on screen")
                return {
                    'success': False,
                    'error': f"Text '{target_text}' not found",
                    'position': None,
                    'confidence': 0
                }
            
            # Use the match with highest confidence
            best_match = max(found_matches, key=lambda x: x['confidence'])
            
            print(f"🎯 Best match: '{best_match['text']}' (confidence: {best_match['confidence']:.2f})")
            
            if click:
                # Add some randomness to click position
                x, y = best_match['position']
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-3, 3)
                final_x = x + offset_x
                final_y = y + offset_y
                
                print(f"🖱️  Moving to ({final_x}, {final_y}) and clicking...")
                pyautogui.moveTo(final_x, final_y, duration=0.2)
                time.sleep(0.1)
                pyautogui.click()
                print(f"✅ Clicked on '{best_match['text']}'")
            
            return {
                'success': True,
                'text_found': best_match['text'],
                'position': best_match['position'],
                'confidence': best_match['confidence'],
                'bounding_box': best_match['bounding_box'],
                'all_matches': found_matches
            }
            
        except Exception as e:
            error_msg = f"Error during text detection: {e}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'position': None,
                'confidence': 0
            }
    
    def continuous_text_search(self, target_text, max_attempts=10, delay=1.0, **kwargs):
        """
        Continuously search for text until found or max attempts reached
        
        Args:
            target_text (str): Text to search for
            max_attempts (int): Maximum number of search attempts
            delay (float): Delay between attempts in seconds
            **kwargs: Additional arguments for findtextonscreen
            
        Returns:
            dict: Result of the search
        """
        print(f"🔄 Starting continuous search for '{target_text}'")
        print(f"📊 Max attempts: {max_attempts}, delay: {delay}s")
        
        for attempt in range(1, max_attempts + 1):
            print(f"\n🔍 Attempt {attempt}/{max_attempts}")
            
            result = self.findtextonscreen(target_text, **kwargs)
            
            if result['success']:
                print(f"🎉 Found '{target_text}' on attempt {attempt}!")
                return result
            
            if attempt < max_attempts:
                print(f"⏳ Waiting {delay}s before next attempt...")
                time.sleep(delay)
        
        print(f"❌ Failed to find '{target_text}' after {max_attempts} attempts")
        return {
            'success': False,
            'error': f"Text not found after {max_attempts} attempts",
            'position': None,
            'confidence': 0
        }
    
    def scan_all_text(self, min_confidence=0.5):
        """
        Scan and display all readable text on screen
        Useful for debugging and seeing what text is detectable
        """
        print("🔍 Scanning all text on screen...")
        
        try:
            screen = self.functions.capture_screen()
            if screen is None:
                print("❌ Failed to capture screen")
                return
            
            screen_rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
            data = pytesseract.image_to_data(screen_rgb, output_type=pytesseract.Output.DICT)
            
            detected_texts = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                confidence = float(data['conf'][i]) / 100.0
                
                if text and confidence >= min_confidence:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    center_x = x + w // 2
                    center_y = y + h // 2
                    
                    detected_texts.append({
                        'text': text,
                        'position': (center_x, center_y),
                        'confidence': confidence
                    })
            
            print(f"\n📊 Found {len(detected_texts)} text elements:")
            print("-" * 60)
            
            for item in sorted(detected_texts, key=lambda x: x['confidence'], reverse=True):
                print(f"'{item['text']}' at {item['position']} (confidence: {item['confidence']:.2f})")
            
            return detected_texts
            
        except Exception as e:
            print(f"❌ Error scanning text: {e}")
            return []


def test_text_detection():
    """Test function to demonstrate text detection capabilities"""
    detector = TextDetector()
    
    print("🧪 Text Detection Test")
    print("=" * 50)
    print("This will test the text detection functionality")
    print()
    
    while True:
        print("\nChoose test mode:")
        print("1. Search for specific text")
        print("2. Continuous search for text") 
        print("3. Scan all readable text on screen")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            target_text = input("Enter text to search for: ").strip()
            if not target_text:
                print("❌ No text entered")
                continue
            
            click_option = input("Click on found text? (y/n, default: y): ").strip().lower()
            should_click = click_option != 'n'
            
            # Wait for user to position and press 'p'
            detector.wait_for_pause_unpause(f"Ready to search for '{target_text}'")
            
            result = detector.findtextonscreen(target_text, click=should_click)
            
            if result['success']:
                print(f"✅ SUCCESS: Found '{result['text_found']}' at {result['position']}")
                print(f"   Confidence: {result['confidence']:.2f}")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        
        elif choice == '2':
            target_text = input("Enter text to search for: ").strip()
            if not target_text:
                print("❌ No text entered")
                continue
            
            max_attempts = input("Max attempts (default: 5): ").strip()
            max_attempts = int(max_attempts) if max_attempts.isdigit() else 5
            
            delay = input("Delay between attempts in seconds (default: 1.0): ").strip()
            delay = float(delay) if delay.replace('.', '').isdigit() else 1.0
            
            click_option = input("Click on found text? (y/n, default: y): ").strip().lower()
            should_click = click_option != 'n'
            
            detector.wait_for_pause_unpause(f"Ready to continuously search for '{target_text}'")
            
            result = detector.continuous_text_search(
                target_text, 
                max_attempts=max_attempts, 
                delay=delay, 
                click=should_click
            )
            
            if result['success']:
                print(f"✅ SUCCESS: Found '{result['text_found']}' at {result['position']}")
            else:
                print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
        
        elif choice == '3':
            min_conf = input("Minimum confidence (0.0-1.0, default: 0.5): ").strip()
            min_conf = float(min_conf) if min_conf.replace('.', '').isdigit() else 0.5
            
            detector.wait_for_pause_unpause("Ready to scan all text on screen")
            detector.scan_all_text(min_confidence=min_conf)
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")


def main():
    """Main function for command-line usage"""
    print("🔍 Text Detection Script")
    print("=" * 50)
    print("Find and interact with text on screen (NPCs, items, interfaces)")
    print()
    
    # Check if required packages are available
    try:
        print("✅ Checking required packages...")
        print("   ✅ OpenCV available")
        print("   ✅ NumPy available")  
        print("   ✅ PyAutoGUI available")
        print("   ✅ Pytesseract available")
        print("   ✅ Pynput available")
        print("   ✅ AutoActionFunctions available")
    except Exception as e:
        print(f"❌ Package check failed: {e}")
        return
    
    # Test tesseract installation
    try:
        pytesseract.get_tesseract_version()
        print("   ✅ Tesseract OCR available")
    except Exception as e:
        print(f"   ⚠️  Tesseract OCR warning: {e}")
        print("      You may need to install Tesseract or set the correct path")
    
    print("\nReady to detect text!")
    test_text_detection()


if __name__ == "__main__":
    main()
